from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel


class LoginResponse(BaseModel):
    mfa_required: bool = False
    mfa_token: Optional[str] = None
    access_token: Optional[str] = None
    token_type: Optional[str] = None
    needs_2fa_setup: bool = False


class MFAVerifyRequest(BaseModel):
    mfa_token: str
    code: str


class TOTPSetupResponse(BaseModel):
    secret: str
    provisioning_uri: str


class TOTPEnableRequest(BaseModel):
    code: str


class TOTPEnableResponse(BaseModel):
    backup_codes: list[str]


class TOTPDisableRequest(BaseModel):
    code: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class UserMeResponse(BaseModel):
    id: uuid.UUID
    username: str
    role: str
    customer_id: Optional[uuid.UUID] = None
    display_name: Optional[str] = None
    totp_enabled: bool
    totp_required: bool

    model_config = {"from_attributes": True}
