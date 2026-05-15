"""
RAG chat endpoints with streaming support.

Full RAG pipeline implementation will be added in Phase 4–5.
"""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user
from app.db.models.user import User
from app.schemas.chat import (
    ChatRequest,
    ConversationResponse,
    ConversationListResponse,
    MessageResponse,
)

router = APIRouter()


@router.post("/", response_model=MessageResponse)
async def send_message(
    data: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Send a message and receive a RAG-augmented response.

    Pipeline (Phase 4–5):
    1. Retrieve relevant chunks via semantic search
    2. Build augmented prompt with context
    3. Send to LLM (Ollama)
    4. Parse response with citations
    5. Store in conversation history
    """
    from app.services.rag_service import RAGService
    service = RAGService(db)
    
    response_dict = await service.chat(
        workspace_id=data.workspace_id,
        query=data.message,
        conversation_id=data.conversation_id,
        model=data.model_name or "llama3",
        user_id=current_user.id
    )
    
    return MessageResponse(**response_dict)


@router.post("/stream")
async def send_message_stream(
    data: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Send a message and receive a streaming RAG response via SSE.

    Uses Server-Sent Events for real-time token streaming.
    """
    from app.services.rag_service import RAGService
    service = RAGService(db)

    return StreamingResponse(
        service.chat_stream(
            workspace_id=data.workspace_id,
            query=data.message,
            conversation_id=data.conversation_id,
            model=data.model_name or "llama3",
            user_id=current_user.id
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all conversations in a workspace for the current user."""
    from sqlalchemy import select, func
    from app.db.models.conversation import Conversation
    
    count_result = await db.execute(select(func.count()).select_from(Conversation).where(Conversation.workspace_id == workspace_id, Conversation.user_id == current_user.id))
    total = count_result.scalar() or 0
    
    result = await db.execute(
        select(Conversation)
        .where(Conversation.workspace_id == workspace_id, Conversation.user_id == current_user.id)
        .order_by(Conversation.created_at.desc())
    )
    conversations = list(result.scalars().all())
    
    return ConversationListResponse(
        conversations=conversations,
        total=total,
        page=1,
        page_size=100,
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific conversation with all messages."""
    from sqlalchemy import select
    from fastapi import HTTPException
    from app.db.models.conversation import Conversation, Message
    
    result = await db.execute(select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == current_user.id))
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    msg_result = await db.execute(select(Message).where(Message.conversation_id == conversation_id).order_by(Message.message_index.asc()))
    messages = list(msg_result.scalars().all())
    
    return ConversationResponse(
        id=conv.id,
        title=conv.title,
        workspace_id=conv.workspace_id,
        user_id=conv.user_id,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        messages=messages
    )
