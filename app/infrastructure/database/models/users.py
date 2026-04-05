from __future__ import annotations
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.models.base import BaseModel, ActiveMixin
from app.domain.enums.enum import UserStatus

if TYPE_CHECKING:
    from app.infrastructure.database.models.user_role import UserRoleModel
    from app.infrastructure.database.models.refresh_tokens import RefreshTokenModel
    from app.infrastructure.database.models.audit import AuditLogModel


class UserModel(BaseModel, ActiveMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(254),
        unique=True,
        nullable=False,
        index=True,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    status: Mapped[UserStatus] = mapped_column(
        SAEnum(UserStatus, name="user_status_enum"),
        default=UserStatus.ACTIVE,
        nullable=False,
        index=True,
    )

    # relationships
    user_roles: Mapped[list[UserRoleModel]] = relationship(
        "UserRoleModel",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
        foreign_keys="[UserRoleModel.user_id]",
    )
    refresh_tokens: Mapped[list[RefreshTokenModel]] = relationship(
        "RefreshTokenModel",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    audit_logs: Mapped[list[AuditLogModel]] = relationship(
        "AuditLogModel",
        back_populates="actor",
        foreign_keys="AuditLogModel.actor_id",
    )
