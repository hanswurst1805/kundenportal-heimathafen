from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import hash_password, require_role
from src.core.database import get_session
from src.models.user import User
from src.schemas.customer import (
    UserCreate,
    UserOut,
    UserReset2FAResponse,
    UserResetPasswordRequest,
    UserUpdate,
)

router = APIRouter(prefix="/users", tags=["intern-users"], dependencies=[Depends(require_role("admin"))])


@router.get("", response_model=list[UserOut])
async def list_users(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).order_by(User.username))
    return result.scalars().all()


@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")
    return user


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(data: UserCreate, session: AsyncSession = Depends(get_session)):
    existing = (
        await session.execute(select(User).where(User.username == data.username))
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "Benutzername ist bereits vergeben")

    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        role=data.role,
        customer_id=data.customer_id,
        display_name=data.display_name,
        totp_required=data.role in ("admin", "user"),
    )
    session.add(user)
    await session.flush()
    return user


@router.patch("/{user_id}", response_model=UserOut)
async def update_user(user_id: uuid.UUID, data: UserUpdate, session: AsyncSession = Depends(get_session)):
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    if "role" in data.model_dump(exclude_unset=True):
        user.totp_required = user.role in ("admin", "user")
    return user


@router.post("/{user_id}/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    user_id: uuid.UUID, data: UserResetPasswordRequest, session: AsyncSession = Depends(get_session)
):
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")
    user.password_hash = hash_password(data.new_password)


@router.post("/{user_id}/reset-2fa", response_model=UserReset2FAResponse)
async def reset_2fa(user_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")
    user.totp_enabled = False
    user.totp_secret = None
    user.backup_codes = None
    return UserReset2FAResponse(totp_enabled=False)
