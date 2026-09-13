from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)

    # Added in Lab 4 (migrated via Alembic).
    description: Mapped[str | None] = mapped_column(String(250), nullable=True)

    # ASSUMPTION (Lab 6 is ambiguous about this field's origin): the Lab 6 curl
    # example and the list_documents agent tool both require a "priority"
    # value that never appears in the Lab 4/5 spec. Adding it here, nullable
    # with a default, migrated in the same Lab 6 migration as ai_summary.
    priority: Mapped[int | None] = mapped_column(Integer, nullable=True, default=1)

    # Added in Lab 6 (migrated via Alembic) — holds the Gemini-generated summary.
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
