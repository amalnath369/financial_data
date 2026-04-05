from __future__ import annotations
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, Enum as SAEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.models.base import BaseModel, ActiveMixin
from app.domain.enums.enum import CategoryType

if TYPE_CHECKING:
    from app.infrastructure.database.models.record import FinancialRecordModel


class CategoryModel(BaseModel, ActiveMixin):
    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        default="",
    )
    category_type: Mapped[CategoryType] = mapped_column(
        SAEnum(CategoryType, name="category_type_enum"),
        nullable=False,
        index=True,
    )
    is_system: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # relationships
    records: Mapped[list[FinancialRecordModel]] = relationship(
        "FinancialRecordModel",
        back_populates="category",
    )
