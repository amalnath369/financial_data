from enum import Enum


class PermissionResource(str, Enum):
    RECORDS = "records"
    USERS = "users"
    CATEGORIES = "categories"
    DASHBOARD = "dashboard"
    ROLES = "roles"


class PermissionAction(str, Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    MANAGE = "manage"


# All valid permission strings — used for seeding + validation
ALL_PERMISSIONS: list[str] = [
    # Records
    "records:create",
    "records:read",
    "records:update",
    "records:delete",
    # Users
    "users:create",
    "users:read",
    "users:update",
    "users:delete",
    # Categories
    "categories:create",
    "categories:read",
    "categories:update",
    "categories:delete",
    # Dashboard
    "dashboard:read",
    # Roles
    "roles:manage",
]