"""
Chunk model — document segments with embedding references.
"""

from sqlalchemy import ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Chunk(Base):
    __tablename__ = "chunks"

    content: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)

    # Reference to vector DB embedding
    embedding_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    # Source location info
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    start_char: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_char: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Chunking metadata
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chunk_method: Mapped[str | None] = mapped_column(String(50), nullable=True)  # recursive | semantic

    # Extra metadata (e.g., section title, heading)
    metadata_json: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True, default=dict)

    # Foreign key
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Relationships
    document = relationship("Document", back_populates="chunks")

    def __repr__(self) -> str:
        return f"<Chunk id={self.id} doc={self.document_id} idx={self.chunk_index}>"
