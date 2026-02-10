from sqlalchemy import String, Integer, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from .db import Base

class FunctionDef(Base):
    __tablename__ = "function_defs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)

    # Descripción "de negocio" (humana)
    business_desc: Mapped[str] = mapped_column(Text)

    # Descripción "técnica" (más formal)
    technical_desc: Mapped[str] = mapped_column(Text)

    input_schema: Mapped[str] = mapped_column(Text)   # JSON string
    output_schema: Mapped[str] = mapped_column(Text)  # JSON string
    enums: Mapped[str] = mapped_column(Text)          # JSON string
    query_examples: Mapped[str] = mapped_column(Text) # JSON string (lista)

    profile_text: Mapped[str] = mapped_column(Text)   # texto usado para embeddings (limpio)
    embedding_json: Mapped[str] = mapped_column(Text) # vector serializado JSON

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
