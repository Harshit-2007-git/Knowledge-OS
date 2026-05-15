"""
Workspace model — project/workspace isolation for multi-tenant support.
"""

from sqlalchemy import ForeignKey, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Workspace(Base):
    __tablename__ = "workspaces"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    settings: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)

    # Relationships
    owner = relationship("User", back_populates="workspaces")
    documents = relationship(
        "Document", back_populates="workspace", lazy="selectin", cascade="all, delete-orphan"
    )
    conversations = relationship(
        "Conversation", back_populates="workspace", lazy="selectin", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Workspace id={self.id} name={self.name}>"
