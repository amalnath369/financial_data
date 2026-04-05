"""initial schema

Revision ID: 868c5a0ee535
Revises:
Create Date: 2026-04-03 00:00:00.000000

"""
from __future__ import annotations
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "868c5a0ee535"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # ── enums (idempotent) ────────────────────────────────────────────────────
    conn.execute(sa.text("""
        DO $$ BEGIN CREATE TYPE user_status_enum AS ENUM ('active', 'inactive');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """))
    conn.execute(sa.text("""
        DO $$ BEGIN CREATE TYPE record_type_enum AS ENUM ('income', 'expense');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """))
    conn.execute(sa.text("""
        DO $$ BEGIN CREATE TYPE category_type_enum AS ENUM ('income', 'expense', 'both');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """))
    conn.execute(sa.text("""
        DO $$ BEGIN CREATE TYPE audit_status_enum AS ENUM ('success', 'failed');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """))
    conn.execute(sa.text("""
        DO $$ BEGIN CREATE TYPE action_type_enum AS ENUM (
            'auth:login','auth:login_failed','auth:logout','auth:token_refresh','auth:register',
            'users:create','users:update','users:delete','users:activate','users:deactivate',
            'users:role_assign','users:role_remove',
            'records:create','records:update','records:delete',
            'categories:create','categories:update','categories:delete',
            'roles:create','roles:update','roles:delete','roles:permission_assign','roles:permission_remove'
        );
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """))

    # ── tables ────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("status", sa.Enum("active", "inactive", name="user_status_enum", create_type=False), nullable=False, server_default="active"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_status", "users", ["status"])
    op.create_index("ix_users_is_active", "users", ["is_active"])
    op.create_index("ix_users_is_deleted", "users", ["is_deleted"])

    op.create_table(
        "roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.String(500), nullable=False, server_default=""),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_roles_name", "roles", ["name"], unique=True)
    op.create_index("ix_roles_is_active", "roles", ["is_active"])
    op.create_index("ix_roles_is_deleted", "roles", ["is_deleted"])

    op.create_table(
        "permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("resource", sa.String(100), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("description", sa.String(500), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.UniqueConstraint("resource", "action", name="uq_permission_resource_action"),
    )
    op.create_index("ix_permissions_resource", "permissions", ["resource"])
    op.create_index("ix_permissions_is_deleted", "permissions", ["is_deleted"])

    op.create_table(
        "user_roles",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("assigned_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    )

    op.create_table(
        "role_permissions",
        sa.Column("role_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("permission_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.String(500), nullable=False, server_default=""),
        sa.Column("category_type", sa.Enum("income", "expense", "both", name="category_type_enum", create_type=False), nullable=False),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_categories_name", "categories", ["name"], unique=True)
    op.create_index("ix_categories_category_type", "categories", ["category_type"])
    op.create_index("ix_categories_is_active", "categories", ["is_active"])
    op.create_index("ix_categories_is_deleted", "categories", ["is_deleted"])

    op.create_table(
        "financial_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("amount", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("record_type", sa.Enum("income", "expense", name="record_type_enum", create_type=False), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("record_date", sa.Date(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("search_vector", postgresql.TSVECTOR(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_financial_records_user_id", "financial_records", ["user_id"])
    op.create_index("ix_financial_records_record_type", "financial_records", ["record_type"])
    op.create_index("ix_financial_records_category_id", "financial_records", ["category_id"])
    op.create_index("ix_financial_records_record_date", "financial_records", ["record_date"])
    op.create_index("ix_financial_records_is_deleted", "financial_records", ["is_deleted"])
    op.create_index("idx_records_user_date", "financial_records", ["user_id", "record_date"],
                    postgresql_where=sa.text("is_deleted = FALSE"))
    op.create_index("idx_records_type_category", "financial_records", ["record_type", "category_id"],
                    postgresql_where=sa.text("is_deleted = FALSE"))
    op.create_index("idx_records_amount", "financial_records", ["amount"],
                    postgresql_where=sa.text("is_deleted = FALSE"))
    op.create_index("idx_records_search_vector", "financial_records", ["search_vector"],
                    postgresql_using="gin")

    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"])
    op.create_index("ix_refresh_tokens_revoked", "refresh_tokens", ["revoked"])

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("actor_email", sa.String(254), nullable=False),
        sa.Column("actor_roles", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("action", sa.Enum(
            "auth:login", "auth:login_failed", "auth:logout", "auth:token_refresh", "auth:register",
            "users:create", "users:update", "users:delete", "users:activate", "users:deactivate",
            "users:role_assign", "users:role_remove",
            "records:create", "records:update", "records:delete",
            "categories:create", "categories:update", "categories:delete",
            "roles:create", "roles:update", "roles:delete", "roles:permission_assign", "roles:permission_remove",
            name="action_type_enum", create_type=False,
        ), nullable=False),
        sa.Column("resource", sa.String(100), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("before", postgresql.JSONB(), nullable=True),
        sa.Column("after", postgresql.JSONB(), nullable=True),
        sa.Column("diff", postgresql.JSONB(), nullable=True),
        sa.Column("request_id", sa.String(100), nullable=False),
        sa.Column("ip_address", sa.String(45), nullable=False),
        sa.Column("user_agent", sa.String(500), nullable=False, server_default=""),
        sa.Column("status", sa.Enum("success", "failed", name="audit_status_enum", create_type=False), nullable=False),
        sa.Column("failure_reason", sa.String(500), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_audit_logs_actor_id", "audit_logs", ["actor_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_resource", "audit_logs", ["resource"])
    op.create_index("ix_audit_logs_resource_id", "audit_logs", ["resource_id"])
    op.create_index("ix_audit_logs_request_id", "audit_logs", ["request_id"])
    op.create_index("ix_audit_logs_status", "audit_logs", ["status"])
    op.create_index("ix_audit_logs_timestamp", "audit_logs", ["timestamp"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("refresh_tokens")
    op.drop_table("financial_records")
    op.drop_table("categories")
    op.drop_table("role_permissions")
    op.drop_table("user_roles")
    op.drop_table("permissions")
    op.drop_table("roles")
    op.drop_table("users")
    op.execute(sa.text("DROP TYPE action_type_enum"))
    op.execute(sa.text("DROP TYPE audit_status_enum"))
    op.execute(sa.text("DROP TYPE category_type_enum"))
    op.execute(sa.text("DROP TYPE record_type_enum"))
    op.execute(sa.text("DROP TYPE user_status_enum"))
