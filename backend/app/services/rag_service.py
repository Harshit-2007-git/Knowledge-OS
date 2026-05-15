import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
import datetime

from app.db.models.conversation import Conversation, Message
from app.vectorstore.chroma_client import get_or_create_collection as get_collection
from app.ml.embeddings import get_embedding_model
from app.ml.llm import get_llm_client          # ← uses factory, picks Groq or Ollama from config

logger = logging.getLogger(__name__)


class RAGService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm = get_llm_client()            # ← Groq by default (LLM_PROVIDER=groq in .env)

    async def get_or_create_conversation(
        self,
        workspace_id: str,
        title: str = "New Conversation",
        conversation_id: str = None,
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
            user_id="anonymous",
        )
        self.db.add(conv)
        await self.db.flush()
        return conv

    async def retrieve_context(
        self, workspace_id: str, query: str, top_k: int = 5
    ) -> list[dict]:
        """Search ChromaDB for relevant chunks."""
        collection = get_collection(workspace_id)
        if not collection:
            return []

        model = get_embedding_model()
        query_embedding = model.encode([query])[0].tolist()

        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
            )
            contexts = []
            if results["documents"] and len(results["documents"]) > 0:
                for i, doc in enumerate(results["documents"][0]):
                    metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                    contexts.append({
                        "text": doc,
                        "metadata": metadata,
                        "distance": (
                            results["distances"][0][i]
                            if "distances" in results and results["distances"]
                            else 0
                        ),
                    })
            return contexts
        except Exception as e:
            logger.error("ChromaDB search failed: %s", e)
            return []

    async def chat(
        self,
        workspace_id: str,
        query: str,
        conversation_id: str = None,
        model: str = None,
        user_id: str = None,
    ) -> dict:
        """Process a chat message, retrieve context, and generate response."""

        # 1. Retrieve context
        contexts = await self.retrieve_context(workspace_id, query)
        context_text = "\n\n---\n\n".join([c["text"] for c in contexts])

        # 2. Prepare conversation
        conv = await self.get_or_create_conversation(
            workspace_id, title=query[:50] + "...", conversation_id=conversation_id
        )
        if user_id:
            conv.user_id = user_id

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

        # 5. Generate LLM response (model arg ignored for Groq — uses GROQ_MODEL from config)
        llm_response = await self.llm.generate_chat(messages)

        # 6. Store AI message
        ai_msg = Message(
            conversation_id=conv.id,
            role="assistant",
            content=llm_response,
            message_index=next_idx + 1,
            model_name=getattr(self.llm, "default_model", model or "groq"),
            citations=[{"metadata": c["metadata"]} for c in contexts] if contexts else None,
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
        """Process a chat message, retrieve context, and stream response tokens."""
        import json

        # 1. Retrieve context
        contexts = await self.retrieve_context(workspace_id, query)
        context_text = "\n\n---\n\n".join([c["text"] for c in contexts])

        # 2. Prepare conversation
        conv = await self.get_or_create_conversation(
            workspace_id, title=query[:50] + "...", conversation_id=conversation_id
        )
        if user_id:
            conv.user_id = user_id

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

        # Yield metadata and start events
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
            citations=[{"metadata": c["metadata"]} for c in contexts] if contexts else None,
        )
        self.db.add(ai_msg)
        await self.db.commit()