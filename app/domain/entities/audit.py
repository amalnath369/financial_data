from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from app.domain.enums.action_type import ActionType
from app.domain.enums.enum import AuditStatus


@dataclass
class AuditLog:
    """
    Audit log domain entity.
    - Immutable once created — no update or delete ever allowed
    - Snapshots actor email + roles at the exact time of action
    - Stores before/after/diff for full traceability
    - Tied to request_id for correlation with structured logs
    """

    id: uuid.UUID
    actor_id: uuid.UUID
    actor_email: str                        
    actor_roles: list[str]                  
    action: ActionType
    resource: str
    resource_id: uuid.UUID | None
    before: dict | None                     # state before change
    after: dict | None                      # state after change
    diff: dict | None                       # only what changed
    request_id: str                         # ties to structured logs
    ip_address: str
    user_agent: str
    status: AuditStatus
    failure_reason: str | None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # ── factories ──────────────────────────────────────────────────────────

    @classmethod
    def create_success(
        cls,
        actor_id: uuid.UUID,
        actor_email: str,
        actor_roles: list[str],
        action: ActionType,
        resource: str,
        request_id: str,
        ip_address: str,
        user_agent: str,
        resource_id: uuid.UUID | None = None,
        before: dict | None = None,
        after: dict | None = None,
        diff: dict | None = None,
    ) -> AuditLog:
        return cls(
            id=uuid.uuid4(),
            actor_id=actor_id,
            actor_email=actor_email,
            actor_roles=actor_roles,
            action=action,
            resource=resource,
            resource_id=resource_id,
            before=before,
            after=after,
            diff=diff,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
            status=AuditStatus.SUCCESS,
            failure_reason=None,
        )

    @classmethod
    def create_failure(
        cls,
        actor_id: uuid.UUID,
        actor_email: str,
        actor_roles: list[str],
        action: ActionType,
        resource: str,
        request_id: str,
        ip_address: str,
        user_agent: str,
        failure_reason: str,
        resource_id: uuid.UUID | None = None,
    ) -> AuditLog:
        return cls(
            id=uuid.uuid4(),
            actor_id=actor_id,
            actor_email=actor_email,
            actor_roles=actor_roles,
            action=action,
            resource=resource,
            resource_id=resource_id,
            before=None,
            after=None,
            diff=None,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
            status=AuditStatus.FAILED,
            failure_reason=failure_reason,
        )

    # ── immutability guard ─────────────────────────────────────────────────

    def __setattr__(self, name: str, value: object) -> None:
        """
        Allow setting during __init__ only.
        After construction, audit logs are immutable.
        """
        if hasattr(self, "_frozen") and self._frozen:
            raise AttributeError("AuditLog is immutable after creation")
        super().__setattr__(name, value)

    def __post_init__(self) -> None:
        object.__setattr__(self, "_frozen", True)

    # ── representation ─────────────────────────────────────────────────────

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AuditLog):
            return NotImplemented
        return self.id == other.id