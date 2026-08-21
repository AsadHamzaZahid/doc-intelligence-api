from app.database import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from sqlalchemy import DateTime, func, String
from sqlalchemy.orm import mapped_column, Mapped


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    email: Mapped[str] = mapped_column(
        String, unique=True, index=True, nullable=False)

    hash_password: Mapped[str] = mapped_column(String, nullable=None)

    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), default=func.now())
