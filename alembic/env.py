from __future__ import annotations
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import settings

# ── Import every model so Alembic can detect them ─────────────────────────
# This must cover every table. The order does not matter.
from app.infrastructure.database.models.base import Base  # noqa: F401
from app.infrastructure.database.models.users import UserModel  # noqa: F401
from app.infrastructure.database.models.roles import RoleModel  # noqa: F401
from app.infrastructure.database.models.permission import PermissionModel  # noqa: F401
from app.infrastructure.database.models.user_role import UserRoleModel  # noqa: F401
from app.infrastructure.database.models.role_permission import RolePermissionModel  # noqa: F401
from app.infrastructure.database.models.record import FinancialRecordModel  # noqa: F401
from app.infrastructure.database.models.category import CategoryModel  # noqa: F401
from app.infrastructure.database.models.refresh_tokens import RefreshTokenModel  # noqa: F401
from app.infrastructure.database.models.audit import AuditLogModel  # noqa: F401

# Alembic config object — gives access to alembic.ini values
config = context.config

# Wire Python logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Use the full SQLAlchemy metadata so autogenerate can diff the schema
target_metadata = Base.metadata

# Override the sqlalchemy.url from settings so the .env file is the
# single source of truth — no duplication in alembic.ini
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)


# ── Offline mode (generates SQL without connecting) ───────────────────────

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# ── Online mode (connects and runs migrations) ────────────────────────────

def do_run_migrations(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,   # migrations never need a pool
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
