import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import datetime

from app.db.models.conversation import Conversation, Message
from app.ml.llm import get_llm_client

logger = logging.getLogger(__name__)


class RAGService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm = get_llm_client()

    async def get_or_create_conversation(
        self,
        workspace_id: str,
        title: str = "New Conversation",
        conversation_id: str = None,
        user_id: str = None,
    ) -> Conversation:
        if conversation_id:
            result = await self.db.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
            conv = result.scalar_one_or_none()
            if conv:
                return conv

        conv = Conversation(
            title=title,
            workspace_id=workspace_id,
            user_id=user_id,  # always use the real user id, never "anonymous"
        )
        self.db.add(conv)
        await self.db.flush()
        return conv

    async def retrieve_context(
        self, workspace_id: str, query: str, top_k: int = 5
    ) -> list[dict]:
        """Search document chunks using PostgreSQL full-text search."""
        from sqlalchemy import select, or_
        from app.db.models.chunk import Chunk
        from app.db.models.document import Document

        keywords = [kw.strip() for kw in query.split() if len(kw.strip()) > 2]
        if not keywords:
            keywords = [query.strip()]

        ilike_conditions = [Chunk.content.ilike(f"%{kw}%") for kw in keywords]

        try:
            stmt = (
                select(Chunk, Document.filename)
                .join(Document, Chunk.document_id == Document.id)
                .where(
                    Document.workspace_id == workspace_id,
                    Document.status == "completed",
                    or_(*ilike_conditions),
                )
                .limit(top_k)
            )
            result = await self.db.execute(stmt)
            rows = result.all()

            contexts = []
            for chunk, filename in rows:
                matched = sum(1 for kw in keywords if kw.lower() in chunk.content.lower())
                score = matched / len(keywords) if keywords else 0
                contexts.append({
                    "text": chunk.content,
                    "metadata": {
                        "chunk_id": chunk.id,
                        "document_id": chunk.document_id,
                        "document_name": filename,
                    },
                    "distance": 1 - score,
                })
            return contexts
        except Exception as e:
            logger.error("PostgreSQL search failed: %s", e)
            return []

    async def chat(
        self,
        workspace_id: str,
        query: str,
        conversation_id: str = None,
        model: str = None,
        user_id: str = None,
    ) -> dict:
        # 1. Retrieve context
        contexts = await self.retrieve_context(workspace_id, query)
        context_text = "\n\n---\n\n".join([c["text"] for c in contexts])

        # 2. Prepare conversation — pass user_id directly
        conv = await self.get_or_create_conversation(
            workspace_id, title=query[:50] + "...",
            conversation_id=conversation_id, user_id=user_id
        )

        # 3. Store user message
        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conv.id)
            .order_by(Message.message_index.desc())
        )
        last_msg = result.scalars().first()
        next_idx = last_msg.message_index + 1 if last_msg else 0

        user_msg = Message(
            conversation_id=conv.id,
            role="user",
            content=query,
            message_index=next_idx,
        )
        self.db.add(user_msg)

        # 4. Construct prompt
        system_prompt = (
            "You are an intelligent knowledge base assistant. "
            "Answer the user's question based strictly on the provided context.\n"
            "If the answer is not contained in the context, say "
            "'I don't have enough information to answer that.'\n\n"
            "Context Information:\n"
            f"{context_text}"
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ]

        # 5. Generate LLM response
        llm_response = await self.llm.generate_chat(messages)

        # 6. Store AI message
        ai_msg = Message(
            conversation_id=conv.id,
            role="assistant",
            content=llm_response,
            message_index=next_idx + 1,
            model_name=getattr(self.llm, "default_model", model or "groq"),
            citations=[{
                "chunk_id": c["metadata"].get("chunk_id", ""),
                "document_id": c["metadata"].get("document_id", ""),
                "document_name": c["metadata"].get("document_name", ""),
                "content": c.get("text", ""),
                "relevance_score": float(1 - c.get("distance", 0)),
                "metadata": c["metadata"],
            } for c in contexts] if contexts else None,
        )
        self.db.add(ai_msg)
        await self.db.commit()
        await self.db.refresh(ai_msg)

        return {
            "id": ai_msg.id,
            "conversation_id": conv.id,
            "role": ai_msg.role,
            "content": ai_msg.content,
            "message_index": ai_msg.message_index,
            "citations": ai_msg.citations,
            "model_name": ai_msg.model_name,
            "created_at": (
                ai_msg.created_at.isoformat()
                if ai_msg.created_at
                else datetime.datetime.utcnow().isoformat()
            ),
        }

    async def chat_stream(
        self,
        workspace_id: str,
        query: str,
        conversation_id: str = None,
        model: str = None,
        user_id: str = None,
    ):
        import json

        # 1. Retrieve context
        contexts = await self.retrieve_context(workspace_id, query)
        context_text = "\n\n---\n\n".join([c["text"] for c in contexts])

        # 2. Prepare conversation — pass user_id directly
        conv = await self.get_or_create_conversation(
            workspace_id, title=query[:50] + "...",
            conversation_id=conversation_id, user_id=user_id
        )

        # 3. Store user message
        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conv.id)
            .order_by(Message.message_index.desc())
        )
        last_msg = result.scalars().first()
        next_idx = last_msg.message_index + 1 if last_msg else 0

        user_msg = Message(
            conversation_id=conv.id,
            role="user",
            content=query,
            message_index=next_idx,
        )
        self.db.add(user_msg)
        await self.db.commit()

        # 4. Construct prompt
        system_prompt = (
            "You are an intelligent knowledge base assistant. "
            "Answer the user's question based strictly on the provided context.\n"
            "If the answer is not contained in the context, say "
            "'I don't have enough information to answer that.'\n\n"
            "Context Information:\n"
            f"{context_text}"
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ]

        yield f"data: {json.dumps({'type': 'metadata', 'conversation_id': conv.id})}\n\n"
        yield f"data: {json.dumps({'type': 'start'})}\n\n"

        # 5. Stream LLM response
        full_response = ""
        try:
            async for chunk in self.llm.generate_chat_stream(messages):
                full_response += chunk
                yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"
        except Exception as e:
            logger.error("Streaming error: %s", e)
            yield f"data: {json.dumps({'type': 'token', 'content': f'[Error: {e}]'})}\n\n"

        yield f"data: {json.dumps({'type': 'end'})}\n\n"

        # 6. Store AI message
        ai_msg = Message(
            conversation_id=conv.id,
            role="assistant",
            content=full_response,
            message_index=next_idx + 1,
            model_name=getattr(self.llm, "default_model", model or "groq"),
            citations=[{
                "chunk_id": c["metadata"].get("chunk_id", ""),
                "document_id": c["metadata"].get("document_id", ""),
                "document_name": c["metadata"].get("document_name", ""),
                "content": c.get("text", ""),
                "relevance_score": float(1 - c.get("distance", 0)),
                "metadata": c["metadata"],
            } for c in contexts] if contexts else None,
        )
        self.db.add(ai_msg)
        await self.db.commit()