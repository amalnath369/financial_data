from __future__ import annotations
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.models.base import Base

if TYPE_CHECKING:
    from app.infrastructure.database.models.roles import RoleModel
    from app.infrastructure.database.models.permission import PermissionModel


class RolePermissionModel(Base):
    __tablename__ = "role_permissions"

    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    )
    permission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # relationships
    role: Mapped[RoleModel] = relationship(
        "RoleModel",
        back_populates="role_permissions",
    )
    permission: Mapped[PermissionModel] = relationship(
        "PermissionModel",
        back_populates="role_permissions",
        lazy="selectin",
    )
