from __future__ import annotations
import uuid

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.entities.user import User
from app.domain.repositories.user_repo import AbstractUserRepository
from app.domain.value_objects.email import Email
from app.infrastructure.database.models.users import UserModel
from app.infrastructure.database.models.user_role import UserRoleModel
from app.infrastructure.database.models.roles import RoleModel
from app.infrastructure.database.models.role_permission import RolePermissionModel
from app.infrastructure.repositories.mappers import map_user


class SQLAlchemyUserRepository(AbstractUserRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _with_roles(self, stmt):
        return stmt.options(
            selectinload(UserModel.user_roles)
            .selectinload(UserRoleModel.role)
            .selectinload(RoleModel.role_permissions)
            .selectinload(RolePermissionModel.permission)
        )

    async def get_by_id(self, id: uuid.UUID) -> User | None:
        result = await self._session.execute(
            self._with_roles(select(UserModel)).where(
                UserModel.id == id,
                UserModel.is_deleted == False,
            )
        )
        m = result.scalar_one_or_none()
        return map_user(m) if m else None

    async def get_by_id_with_roles(self, id: uuid.UUID) -> User | None:
        result = await self._session.execute(
            self._with_roles(select(UserModel)).where(
                UserModel.id == id,
                UserModel.is_deleted == False,
            )
        )
        m = result.scalar_one_or_none()
        return map_user(m) if m else None

    async def get_by_email(self, email: Email) -> User | None:
        result = await self._session.execute(
            self._with_roles(select(UserModel)).where(
                UserModel.email == str(email),
                UserModel.is_deleted == False,
            )
        )
        m = result.scalar_one_or_none()
        return map_user(m) if m else None

    async def get_active_by_id(self, id: uuid.UUID) -> User | None:
        result = await self._session.execute(
            self._with_roles(select(UserModel)).where(
                UserModel.id == id,
                UserModel.is_deleted == False,
                UserModel.is_active == True,
            )
        )
        m = result.scalar_one_or_none()
        return map_user(m) if m else None

    async def exists_by_email(self, email: Email) -> bool:
        result = await self._session.execute(
            select(func.count()).select_from(UserModel).where(
                UserModel.email == str(email),
                UserModel.is_deleted == False,
            )
        )
        return result.scalar_one() > 0

    async def get_all(
        self,
        page: int,
        page_size: int,
        is_deleted: bool = False,
        search: str | None = None,
    ) -> tuple[list[User], int]:
        stmt = (
            self._with_roles(select(UserModel))
            .where(UserModel.is_deleted == is_deleted)
        )

        if search:
            pattern = f"%{search.lower()}%"
            stmt = stmt.where(
                or_(
                    UserModel.full_name.ilike(pattern),
                    UserModel.email.ilike(pattern),
                )
            )

        # total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await self._session.scalar(count_stmt)

        # paginated results
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        result = await self._session.execute(stmt)
        users = [map_user(m) for m in result.scalars().all()]
        return users, total or 0

    async def add(self, user: User) -> User:
        m = UserModel(
            id=user.id,
            email=str(user.email),
            hashed_password=user.password.hashed,
            full_name=user.full_name,
            status=user.status,
            is_deleted=user.is_deleted,
            is_active=True,
        )
        self._session.add(m)
        await self._session.flush()
        return user

    async def update(self, user: User) -> User:
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user.id)
        )
        m = result.scalar_one()
        m.email = str(user.email)
        m.hashed_password = user.password.hashed
        m.full_name = user.full_name
        m.status = user.status
        m.is_active = user.is_active
        m.is_deleted = user.is_deleted
        m.deleted_at = user.deleted_at
        m.deleted_by = user.deleted_by
        await self._session.flush()
        return user

    async def delete(self, user: User) -> None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user.id)
        )
        m = result.scalar_one()
        await self._session.delete(m)
        await self._session.flush()

    async def assign_role(self, user_id: uuid.UUID, role_id: uuid.UUID) -> None:
        # idempotent — skip if already assigned
        exists = await self._session.execute(
            select(func.count()).select_from(UserRoleModel).where(
                UserRoleModel.user_id == user_id,
                UserRoleModel.role_id == role_id,
            )
        )
        if exists.scalar_one() == 0:
            self._session.add(UserRoleModel(user_id=user_id, role_id=role_id))
            await self._session.flush()

    async def remove_role(self, user_id: uuid.UUID, role_id: uuid.UUID) -> None:
        result = await self._session.execute(
            select(UserRoleModel).where(
                UserRoleModel.user_id == user_id,
                UserRoleModel.role_id == role_id,
            )
        )
        m = result.scalar_one_or_none()
        if m:
            await self._session.delete(m)
            await self._session.flush()