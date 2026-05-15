"""
Conversation and Message models — chat history with RAG context.
"""

from sqlalchemy import ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Conversation(Base):
    __tablename__ = "conversations"

    title: Mapped[str] = mapped_column(String(500), default="New Chat", server_default="New Chat")
    model_name: Mapped[str] = mapped_column(String(100), nullable=True)

    # Foreign keys
    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Relationships
    workspace = relationship("Workspace", back_populates="conversations")
    user = relationship("User", back_populates="conversations")
    messages = relationship(
        "Message",
        back_populates="conversation",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="Message.message_index",
    )

    def __repr__(self) -> str:
        return f"<Conversation id={self.id} title={self.title}>"


class Message(Base):
    __tablename__ = "messages"

    # Role: user | assistant | system
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_index: Mapped[int] = mapped_column(Integer, nullable=False)

    # Token usage tracking
    prompt_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # RAG context — citations stored as JSON array
    citations: Mapped[list | None] = mapped_column(JSON, nullable=True)
    context_chunks: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Model used for this response
    model_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Foreign key
    conversation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message id={self.id} role={self.role} idx={self.message_index}>"
