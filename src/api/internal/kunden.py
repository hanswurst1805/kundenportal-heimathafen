from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import require_role
from src.core.database import get_session
from src.models.customer import Customer
from src.schemas.customer import CustomerCreate, CustomerOut, CustomerUpdate

router = APIRouter(prefix="/kunden", tags=["intern-kunden"], dependencies=[Depends(require_role("user", "admin"))])


@router.get("", response_model=list[CustomerOut])
async def list_kunden(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Customer).order_by(Customer.name))
    return result.scalars().all()


@router.get("/{customer_id}", response_model=CustomerOut)
async def get_kunde(customer_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    customer = await session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")
    return customer


@router.post("", response_model=CustomerOut, status_code=status.HTTP_201_CREATED)
async def create_kunde(data: CustomerCreate, session: AsyncSession = Depends(get_session)):
    customer = Customer(**data.model_dump())
    session.add(customer)
    await session.flush()
    return customer


@router.patch("/{customer_id}", response_model=CustomerOut)
async def update_kunde(
    customer_id: uuid.UUID, data: CustomerUpdate, session: AsyncSession = Depends(get_session)
):
    customer = await session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(customer, field, value)
    return customer
