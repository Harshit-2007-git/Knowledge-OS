"""
Document model — uploaded files with processing status tracking.
"""

from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Document(Base):
    __tablename__ = "documents"

    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=True)
    file_extension: Mapped[str] = mapped_column(String(20), nullable=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Processing status: pending | processing | completed | failed
    status: Mapped[str] = mapped_column(
        String(50), default="pending", server_default="pending", nullable=False, index=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Extracted content
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    # Metadata
    metadata_json: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True, default=dict)

    # Foreign keys
    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    uploaded_by: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    workspace = relationship("Workspace", back_populates="documents")
    chunks = relationship(
        "Chunk", back_populates="document", lazy="selectin", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Document id={self.id} filename={self.original_filename} status={self.status}>"
