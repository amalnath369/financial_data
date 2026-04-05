from __future__ import annotations
from dataclasses import dataclass


@dataclass
class RegisterDTO:
    email: str
    password: str
    full_name: str


@dataclass
class LoginDTO:
    email: str
    password: str
    ip_address: str
    user_agent: str
    request_id: str = ""


@dataclass
class TokenDTO:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@dataclass
class RefreshDTO:
    refresh_token: str
    ip_address: str
    user_agent: str
    request_id: str = ""


@dataclass
class LogoutDTO:
    access_token: str
    refresh_token: str
    user_id: str