from __future__ import annotations
import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.entities.role import Role
from app.domain.entities.permission import Permission
from app.domain.repositories.role_repo import AbstractRoleRepository
from app.domain.repositories.permission_repo import AbstractPermissionRepository
from app.infrastructure.database.models.roles import RoleModel
from app.infrastructure.database.models.permission import PermissionModel
from app.infrastructure.database.models.role_permission import RolePermissionModel
from app.infrastructure.repositories.mappers import map_role, map_permission


class SQLAlchemyRoleRepository(AbstractRoleRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> Role | None:
        result = await self._session.execute(
            select(RoleModel)
            .options(selectinload(RoleModel.role_permissions).selectinload(RolePermissionModel.permission))
            .where(RoleModel.id == id, RoleModel.is_deleted == False)
        )
        m = result.scalar_one_or_none()
        return map_role(m) if m else None

    async def get_by_id_with_permissions(self, id: uuid.UUID) -> Role | None:
        return await self.get_by_id(id)

    async def get_by_name(self, name: str) -> Role | None:
        result = await self._session.execute(
            select(RoleModel)
            .options(selectinload(RoleModel.role_permissions).selectinload(RolePermissionModel.permission))
            .where(
                func.lower(RoleModel.name) == name.strip().lower(),
                RoleModel.is_deleted == False,
            )
        )
        m = result.scalar_one_or_none()
        return map_role(m) if m else None

    async def get_all(
        self,
        page: int = 1,
        page_size: int = 50,
        include_inactive: bool = False,
    ) -> tuple[list[Role], int]:
        stmt = (
            select(RoleModel)
            .options(selectinload(RoleModel.role_permissions).selectinload(RolePermissionModel.permission))
            .where(RoleModel.is_deleted == False)
        )
        if not include_inactive:
            stmt = stmt.where(RoleModel.is_active == True)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await self._session.scalar(count_stmt)

        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        result = await self._session.execute(stmt)
        return [map_role(m) for m in result.scalars().all()], total or 0

    async def exists_by_name(self, name: str) -> bool:
        result = await self._session.execute(
            select(func.count()).select_from(RoleModel).where(
                func.lower(RoleModel.name) == name.strip().lower(),
                RoleModel.is_deleted == False,
            )
        )
        return result.scalar_one() > 0

    async def assign_permission(self, role_id: uuid.UUID, permission_id: uuid.UUID) -> None:
        exists = await self._session.execute(
            select(func.count()).select_from(RolePermissionModel).where(
                RolePermissionModel.role_id == role_id,
                RolePermissionModel.permission_id == permission_id,
            )
        )
        if exists.scalar_one() == 0:
            self._session.add(RolePermissionModel(role_id=role_id, permission_id=permission_id))
            await self._session.flush()

    async def remove_permission(self, role_id: uuid.UUID, permission_id: uuid.UUID) -> None:
        result = await self._session.execute(
            select(RolePermissionModel).where(
                RolePermissionModel.role_id == role_id,
                RolePermissionModel.permission_id == permission_id,
            )
        )
        m = result.scalar_one_or_none()
        if m:
            await self._session.delete(m)
            await self._session.flush()

    async def get_by_ids(self, ids: list[uuid.UUID]) -> list[Role]:
        result = await self._session.execute(
            select(RoleModel)
            .options(selectinload(RoleModel.role_permissions).selectinload(RolePermissionModel.permission))
            .where(RoleModel.id.in_(ids), RoleModel.is_deleted == False)
        )
        return [map_role(m) for m in result.scalars().all()]

    async def add(self, role: Role) -> Role:
        m = RoleModel(
            id=role.id,
            name=role.name,
            description=role.description,
            is_active=role.is_active,
        )
        self._session.add(m)
        await self._session.flush()
        return role

    async def update(self, role: Role) -> Role:
        result = await self._session.execute(
            select(RoleModel).where(RoleModel.id == role.id)
        )
        m = result.scalar_one()
        m.name = role.name
        m.description = role.description
        m.is_active = role.is_active
        m.is_deleted = role.is_deleted
        m.deleted_at = role.deleted_at
        m.deleted_by = role.deleted_by
        await self._session.flush()
        return role

    async def delete(self, role: Role) -> None:
        result = await self._session.execute(
            select(RoleModel).where(RoleModel.id == role.id)
        )
        m = result.scalar_one()
        await self._session.delete(m)
        await self._session.flush()


class SQLAlchemyPermissionRepository(AbstractPermissionRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> Permission | None:
        result = await self._session.execute(
            select(PermissionModel).where(PermissionModel.id == id)
        )
        m = result.scalar_one_or_none()
        return map_permission(m) if m else None

    async def get_by_codename(self, codename: str) -> Permission | None:
        resource, _, action = codename.partition(":")
        result = await self._session.execute(
            select(PermissionModel).where(
                PermissionModel.resource == resource,
                PermissionModel.action == action,
            )
        )
        m = result.scalar_one_or_none()
        return map_permission(m) if m else None

    async def get_all(self) -> list[Permission]:
        result = await self._session.execute(
            select(PermissionModel).where(PermissionModel.is_deleted == False)
        )
        return [map_permission(m) for m in result.scalars().all()]

    async def get_by_ids(self, ids: list[uuid.UUID]) -> list[Permission]:
        result = await self._session.execute(
            select(PermissionModel).where(
                PermissionModel.id.in_(ids),
                PermissionModel.is_deleted == False,
            )
        )
        return [map_permission(m) for m in result.scalars().all()]

    async def exists_by_codename(self, codename: str) -> bool:
        resource, _, action = codename.partition(":")
        result = await self._session.execute(
            select(func.count()).select_from(PermissionModel).where(
                PermissionModel.resource == resource,
                PermissionModel.action == action,
            )
        )
        return result.scalar_one() > 0

    async def bulk_create(self, permissions: list[Permission]) -> None:
        for p in permissions:
            exists = await self.exists_by_codename(p.codename)
            if not exists:
                self._session.add(PermissionModel(
                    id=p.id,
                    resource=p.resource,
                    action=p.action,
                    description=p.description,
                ))
        await self._session.flush()

    async def add(self, permission: Permission) -> Permission:
        m = PermissionModel(
            id=permission.id,
            resource=permission.resource,
            action=permission.action,
            description=permission.description,
        )
        self._session.add(m)
        await self._session.flush()
        return permission

    async def update(self, permission: Permission) -> Permission:
        result = await self._session.execute(
            select(PermissionModel).where(PermissionModel.id == permission.id)
        )
        m = result.scalar_one()
        m.description = permission.description
        await self._session.flush()
        return permission

    async def delete(self, permission: Permission) -> None:
        result = await self._session.execute(
            select(PermissionModel).where(PermissionModel.id == permission.id)
        )
        m = result.scalar_one()
        await self._session.delete(m)
        await self._session.flush()