from __future__ import annotations
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.models.base import Base
from app.domain.enums.action_type import ActionType
from app.domain.enums.enum import AuditStatus

if TYPE_CHECKING:
    from app.infrastructure.database.models.users import UserModel


class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    actor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    actor_email: Mapped[str] = mapped_column(String(254), nullable=False)
    actor_roles: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    action: Mapped[ActionType] = mapped_column(
        SAEnum(ActionType, name="action_type_enum"),
        nullable=False,
        index=True,
    )
    resource: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    before: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    after: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    diff: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    request_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    user_agent: Mapped[str] = mapped_column(String(500), nullable=False, default="")

    status: Mapped[AuditStatus] = mapped_column(
        SAEnum(AuditStatus, name="audit_status_enum"),
        nullable=False,
        index=True,
    )
    failure_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    actor: Mapped[UserModel | None] = relationship(
        "UserModel",
        back_populates="audit_logs",
        foreign_keys=[actor_id],
    )
