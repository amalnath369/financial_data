from __future__ import annotations
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.models.base import BaseModel, ActiveMixin

if TYPE_CHECKING:
    from app.infrastructure.database.models.user_role import UserRoleModel
    from app.infrastructure.database.models.role_permission import RolePermissionModel


class RoleModel(BaseModel, ActiveMixin):
    __tablename__ = "roles"

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

    # relationships
    user_roles: Mapped[list[UserRoleModel]] = relationship(
        "UserRoleModel",
        back_populates="role",
        cascade="all, delete-orphan",
    )
    role_permissions: Mapped[list[RolePermissionModel]] = relationship(
        "RolePermissionModel",
        back_populates="role",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
