# Import every model here so SQLAlchemy's mapper registry is always complete.
# Any file that imports one model from this package will trigger all registrations.
from app.infrastructure.database.models.users import UserModel
from app.infrastructure.database.models.roles import RoleModel
from app.infrastructure.database.models.permission import PermissionModel
from app.infrastructure.database.models.user_role import UserRoleModel
from app.infrastructure.database.models.role_permission import RolePermissionModel
from app.infrastructure.database.models.record import FinancialRecordModel
from app.infrastructure.database.models.category import CategoryModel
from app.infrastructure.database.models.refresh_tokens import RefreshTokenModel
from app.infrastructure.database.models.audit import AuditLogModel

__all__ = [
    "UserModel",
    "RoleModel",
    "PermissionModel",
    "UserRoleModel",
    "RolePermissionModel",
    "FinancialRecordModel",
    "CategoryModel",
    "RefreshTokenModel",
    "AuditLogModel",
]
