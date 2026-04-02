from __future__ import annotations

from app.domain.entities.user import User
from app.domain.entities.audit import AuditLog
from app.domain.repositories.uow import AbstractUnitOfWork
from app.domain.value_objects.email import Email
from app.domain.enums.action_type import ActionType
from app.application.use_cases.users.dtos import CreateUserDTO


class CreateUserUseCase:
    """
    Admin creates a new user with explicit role assignment.
    - Validates email uniqueness
    - Validates roles exist
    - Creates user, assigns roles
    - Logs audit with full after snapshot
    """

    def __init__(self, uow: AbstractUnitOfWork) -> None:
        self._uow = uow

    async def execute(
        self,
        dto: CreateUserDTO,
        actor: User,
        request_id: str,
        ip_address: str,
        user_agent: str,
    ) -> User:
        async with self._uow as uow:
            # 1. email uniqueness
            email = Email(dto.email)
            if await uow.users.exists_by_email(email):
                raise ValueError(f"Email {dto.email!r} already exists")

            # 2. validate roles exist
            roles = []
            for role_name in dto.role_names:
                role = await uow.roles.get_by_name(role_name)
                if not role:
                    raise ValueError(f"Role {role_name!r} does not exist")
                roles.append(role)

            # 3. create user
            user = User.create(
                email=dto.email,
                password=dto.password,
                full_name=dto.full_name,
            )
            for role in roles:
                user.assign_role(role)

            await uow.users.add(user)

            # 4. audit
            audit = AuditLog.create_success(
                actor_id=actor.id,
                actor_email=str(actor.email),
                actor_roles=actor.get_role_names(),
                action=ActionType.USERS_CREATE,
                resource="users",
                resource_id=user.id,
                request_id=request_id,
                ip_address=ip_address,
                user_agent=user_agent,
                after={
                    "id": str(user.id),
                    "email": str(user.email),
                    "full_name": user.full_name,
                    "roles": user.get_role_names(),
                },
            )
            await uow.audit.log(audit)
            await uow.commit()
            return user