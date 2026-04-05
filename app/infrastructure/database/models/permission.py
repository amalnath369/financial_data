from __future__ import annotations
from typing import TYPE_CHECKING

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.models.base import BaseModel

if TYPE_CHECKING:
    from app.infrastructure.database.models.role_permission import RolePermissionModel


class PermissionModel(BaseModel):
    __tablename__ = "permissions"

    __table_args__ = (
        UniqueConstraint("resource", "action", name="uq_permission_resource_action"),
    )

    resource: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False, default="")

    # relationships
    role_permissions: Mapped[list[RolePermissionModel]] = relationship(
        "RolePermissionModel",
        back_populates="permission",
        cascade="all, delete-orphan",
    )
