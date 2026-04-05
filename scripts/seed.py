"""
Seed script — run once after migrations to populate permissions, roles,
and system categories.

Usage:
    python -m scripts.seed
"""
from __future__ import annotations
import asyncio
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums.permission_enum import ALL_PERMISSIONS
from app.domain.enums.enum import CategoryType
from app.infrastructure.database.session import AsyncSessionFactory
from app.infrastructure.database.models import (  # registers all models in SA registry
    PermissionModel,
    RoleModel,
    RolePermissionModel,
    CategoryModel,
)
from sqlalchemy import select, func


# ── permission + role definitions ─────────────────────────────────────────

ROLE_PERMISSIONS: dict[str, list[str]] = {
    "admin": ALL_PERMISSIONS,          # all permissions
    "analyst": [
        "records:create",
        "records:read",
        "records:update",
        "records:delete",
        "categories:read",
        "dashboard:read",
    ],
    "viewer": [
        "records:read",
        "categories:read",
        "dashboard:read",
    ],
}

SYSTEM_CATEGORIES = [
    ("Salary", CategoryType.INCOME, "Regular employment income"),
    ("Freelance", CategoryType.INCOME, "Freelance or contract work"),
    ("Investment", CategoryType.INCOME, "Dividends, interest, capital gains"),
    ("Other Income", CategoryType.INCOME, "Miscellaneous income"),
    ("Housing", CategoryType.EXPENSE, "Rent, mortgage, utilities"),
    ("Food & Dining", CategoryType.EXPENSE, "Groceries and restaurants"),
    ("Transport", CategoryType.EXPENSE, "Fuel, public transit, parking"),
    ("Healthcare", CategoryType.EXPENSE, "Medical, dental, pharmacy"),
    ("Entertainment", CategoryType.EXPENSE, "Movies, subscriptions, hobbies"),
    ("Shopping", CategoryType.EXPENSE, "Clothing, electronics, misc"),
    ("Education", CategoryType.EXPENSE, "Courses, books, tuition"),
    ("Other Expense", CategoryType.EXPENSE, "Miscellaneous expenses"),
    ("Transfer", CategoryType.BOTH, "Transfers between accounts"),
]


async def seed_permissions(session: AsyncSession) -> dict[str, uuid.UUID]:
    """Upsert all permissions. Returns {codename: id} mapping."""
    codename_to_id: dict[str, uuid.UUID] = {}

    for codename in ALL_PERMISSIONS:
        resource, _, action = codename.partition(":")
        # check existence
        result = await session.execute(
            select(PermissionModel).where(
                PermissionModel.resource == resource,
                PermissionModel.action == action,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            codename_to_id[codename] = existing.id
        else:
            perm = PermissionModel(
                id=uuid.uuid4(),
                resource=resource,
                action=action,
                description=f"Allows {action} on {resource}",
            )
            session.add(perm)
            await session.flush()
            codename_to_id[codename] = perm.id
            print(f"  + permission: {codename}")

    return codename_to_id


async def seed_roles(
    session: AsyncSession,
    codename_to_id: dict[str, uuid.UUID],
) -> None:
    """Upsert admin / analyst / viewer roles with their permission sets."""
    for role_name, permissions in ROLE_PERMISSIONS.items():
        result = await session.execute(
            select(RoleModel).where(RoleModel.name == role_name)
        )
        role = result.scalar_one_or_none()

        if not role:
            role = RoleModel(
                id=uuid.uuid4(),
                name=role_name,
                description=f"Built-in {role_name} role",
                is_active=True,
            )
            session.add(role)
            await session.flush()
            print(f"  + role: {role_name}")
        else:
            print(f"  ~ role exists: {role_name}")

        # sync role_permissions junction
        for codename in permissions:
            perm_id = codename_to_id.get(codename)
            if not perm_id:
                continue
            exists = await session.execute(
                select(func.count()).select_from(RolePermissionModel).where(
                    RolePermissionModel.role_id == role.id,
                    RolePermissionModel.permission_id == perm_id,
                )
            )
            if exists.scalar_one() == 0:
                session.add(RolePermissionModel(role_id=role.id, permission_id=perm_id))


async def seed_categories(session: AsyncSession) -> None:
    """Upsert system categories."""
    for name, cat_type, description in SYSTEM_CATEGORIES:
        result = await session.execute(
            select(CategoryModel).where(
                func.lower(CategoryModel.name) == name.lower()
            )
        )
        if result.scalar_one_or_none():
            continue
        session.add(CategoryModel(
            id=uuid.uuid4(),
            name=name,
            category_type=cat_type,
            description=description,
            is_system=True,
            is_active=True,
        ))
        print(f"  + category: {name}")


async def main() -> None:
    print("Seeding database…")
    async with AsyncSessionFactory() as session:
        print("\n[permissions]")
        codename_to_id = await seed_permissions(session)

        print("\n[roles]")
        await seed_roles(session, codename_to_id)

        print("\n[system categories]")
        await seed_categories(session)

        await session.commit()

    print("\nSeed complete.")


if __name__ == "__main__":
    asyncio.run(main())
