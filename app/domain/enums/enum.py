from enum import Enum
 
 
class RecordType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"


class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class CategoryType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"
    BOTH = "both"


class AuditStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"