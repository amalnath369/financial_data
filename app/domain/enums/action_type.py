from enum import Enum


class ActionType(str, Enum):
    # Auth
    AUTH_LOGIN = "auth:login"
    AUTH_LOGIN_FAILED = "auth:login_failed"
    AUTH_LOGOUT = "auth:logout"
    AUTH_TOKEN_REFRESH = "auth:token_refresh"
    AUTH_REGISTER = "auth:register"

    # Users
    USERS_CREATE = "users:create"
    USERS_UPDATE = "users:update"
    USERS_DELETE = "users:delete"
    USERS_ACTIVATE = "users:activate"
    USERS_DEACTIVATE = "users:deactivate"
    USERS_ROLE_ASSIGN = "users:role_assign"
    USERS_ROLE_REMOVE = "users:role_remove"

    # Records
    RECORDS_CREATE = "records:create"
    RECORDS_UPDATE = "records:update"
    RECORDS_DELETE = "records:delete"

    # Categories
    CATEGORIES_CREATE = "categories:create"
    CATEGORIES_UPDATE = "categories:update"
    CATEGORIES_DELETE = "categories:delete"

    # Roles
    ROLES_CREATE = "roles:create"
    ROLES_UPDATE = "roles:update"
    ROLES_DELETE = "roles:delete"
    ROLES_PERMISSION_ASSIGN = "roles:permission_assign"
    ROLES_PERMISSION_REMOVE = "roles:permission_remove"