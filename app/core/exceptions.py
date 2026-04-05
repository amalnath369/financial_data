from __future__ import annotations


class AppError(Exception):
    """Base for all application-level errors."""
    status_code: int = 500
    detail: str = "Internal server error"


class NotFoundError(AppError):
    status_code = 404

    def __init__(self, detail: str = "Resource not found") -> None:
        self.detail = detail
        super().__init__(detail)


class ConflictError(AppError):
    status_code = 409

    def __init__(self, detail: str = "Resource already exists") -> None:
        self.detail = detail
        super().__init__(detail)


class AuthenticationError(AppError):
    status_code = 401

    def __init__(self, detail: str = "Authentication required") -> None:
        self.detail = detail
        super().__init__(detail)


class AuthorizationError(AppError):
    status_code = 403

    def __init__(self, detail: str = "Insufficient permissions") -> None:
        self.detail = detail
        super().__init__(detail)


class ValidationError(AppError):
    status_code = 422

    def __init__(self, detail: str = "Validation failed") -> None:
        self.detail = detail
        super().__init__(detail)
