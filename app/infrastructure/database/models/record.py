from __future__ import annotations
import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date, ForeignKey, Index, Numeric, String,
    Enum as SAEnum, Text,
)
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.models.base import BaseModel
from app.domain.enums.enum import RecordType

if TYPE_CHECKING:
    from app.infrastructure.database.models.users import UserModel
    from app.infrastructure.database.models.category import CategoryModel


class FinancialRecordModel(BaseModel):
    __tablename__ = "financial_records"

    __table_args__ = (
        Index(
            "idx_records_user_date",
            "user_id", "record_date",
            postgresql_where="is_deleted = FALSE",
        ),
        Index(
            "idx_records_type_category",
            "record_type", "category_id",
            postgresql_where="is_deleted = FALSE",
        ),
        Index(
            "idx_records_amount",
            "amount",
            postgresql_where="is_deleted = FALSE",
        ),
        Index(
            "idx_records_search_vector",
            "search_vector",
            postgresql_using="gin",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    amount: Mapped[float] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=False,
    )
    record_type: Mapped[RecordType] = mapped_column(
        SAEnum(RecordType, name="record_type_enum"),
        nullable=False,
        index=True,
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    record_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    search_vector: Mapped[str | None] = mapped_column(
        TSVECTOR,
        nullable=True,
    )

    # relationships
    user: Mapped[UserModel] = relationship(
        "UserModel",
        foreign_keys=[user_id],
    )
    category: Mapped[CategoryModel] = relationship(
        "CategoryModel",
        back_populates="records",
        lazy="selectin",
    )
