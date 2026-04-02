from __future__ import annotations

from app.domain.entities.user import User
from app.domain.repositories.uow import AbstractUnitOfWork
from app.domain.value_objects.email import Email
from app.domain.enums.action_type import ActionType
from app.domain.entities.audit import AuditLog
from app.application.use_cases.auth.dtos import RegisterDTO


class RegisterUseCase:
    """
    Register a new user.
    - Validates email uniqueness
    - Creates user via User.create() — validates email + password value objects
    - Assigns default viewer role
    - Logs audit entry
    - All in one atomic UoW transaction
    """

    def __init__(self, uow: AbstractUnitOfWork) -> None:
        self._uow = uow

    async def execute(
        self,
        dto: RegisterDTO,
        request_id: str,
        ip_address: str,
        user_agent: str,
    ) -> User:
        async with self._uow as uow:
            # 1. check email uniqueness
            email = Email(dto.email)
            if await uow.users.exists_by_email(email):
                raise ValueError(f"Email {dto.email!r} is already registered")

            # 2. create user — value objects validate email + password
            user = User.create(
                email=dto.email,
                password=dto.password,
                full_name=dto.full_name,
            )

            # 3. assign default viewer role
            viewer_role = await uow.roles.get_by_name("viewer")
            if viewer_role:
                user.assign_role(viewer_role)

            # 4. persist
            await uow.users.add(user)

            # 5. audit
            audit = AuditLog.create_success(
                actor_id=user.id,
                actor_email=str(user.email),
                actor_roles=user.get_role_names(),
                action=ActionType.AUTH_REGISTER,
                resource="users",
                resource_id=user.id,
                request_id=request_id,
                ip_address=ip_address,
                user_agent=user_agent,
                after={
                    "id": str(user.id),
                    "email": str(user.email),
                    "full_name": user.full_name,
                },
            )
            await uow.audit.log(audit)

            await uow.commit()
            return user