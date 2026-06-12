from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel


class CustomerOut(BaseModel):
    id: uuid.UUID
    kundennummer: str
    name: str
    short_name: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    is_active: bool

    model_config = {"from_attributes": True}


class CustomerCreate(BaseModel):
    kundennummer: str
    name: str
    short_name: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    short_name: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None


class UserOut(BaseModel):
    id: uuid.UUID
    username: str
    role: str
    customer_id: Optional[uuid.UUID] = None
    display_name: Optional[str] = None
    is_active: bool
    totp_enabled: bool
    totp_required: bool

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    username: str
    password: str
    role: str
    customer_id: Optional[uuid.UUID] = None
    display_name: Optional[str] = None


class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[str] = None
    customer_id: Optional[uuid.UUID] = None


class UserResetPasswordRequest(BaseModel):
    new_password: str


class UserReset2FAResponse(BaseModel):
    totp_enabled: bool = False
