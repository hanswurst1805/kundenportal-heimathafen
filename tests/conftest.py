"""Pytest-Fixtures fuer die Integrationstests.

Die Tests laufen gegen eine **laufende** API-Instanz (Default
`http://localhost:8000`, ueberschreibbar via Umgebungsvariable `BASE_URL`) und
setzen eine **frische** Datenbank voraus (nur Bootstrap-Admin + die per
Migration `0002` geseedeten StatusRegeln, keine Demo-Daten). Grund: der Admin
durchlaeuft genau einmal das 2FA-Setup; das dabei erzeugte TOTP-Secret laesst
sich nachtraeglich nicht wiederherstellen.

Empfohlener Ablauf (im API-Container):
    alembic downgrade base && alembic upgrade head
    # API neu starten (lifespan legt Bootstrap-Admin an)
    pytest tests/

Das Admin-Passwort wird aus `INITIAL_ADMIN_PASSWORD` gelesen (Default
`change-me`, passend zu `.env.example`).
"""

from __future__ import annotations

import os
import uuid

import httpx
import pyotp
import pytest_asyncio

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")
ADMIN_PW = os.environ.get("INITIAL_ADMIN_PASSWORD", "change-me")


def unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


async def _enable_2fa(client: httpx.AsyncClient, token: str) -> str:
    """Fuehrt 2FA-Setup+Enable fuer den per `token` authentifizierten Benutzer
    durch und gibt das TOTP-Secret zurueck."""
    headers = {"Authorization": f"Bearer {token}"}
    r = await client.post("/auth/2fa/setup", headers=headers)
    r.raise_for_status()
    secret = r.json()["secret"]
    r = await client.post("/auth/2fa/enable", headers=headers, json={"code": pyotp.TOTP(secret).now()})
    r.raise_for_status()
    return secret


async def _login_with_2fa(client: httpx.AsyncClient, username: str, password: str, secret: str) -> str:
    r = await client.post("/auth/login", data={"username": username, "password": password})
    r.raise_for_status()
    mfa_token = r.json()["mfa_token"]
    r = await client.post(
        "/auth/2fa/verify", json={"mfa_token": mfa_token, "code": pyotp.TOTP(secret).now()}
    )
    r.raise_for_status()
    return r.json()["access_token"]


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def client():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as c:
        yield c


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def admin_token(client: httpx.AsyncClient) -> str:
    """Admin-Login inkl. einmaligem 2FA-Setup (setzt frische DB voraus)."""
    r = await client.post("/auth/login", data={"username": "admin", "password": ADMIN_PW})
    r.raise_for_status()
    data = r.json()
    if not data.get("needs_2fa_setup"):
        raise RuntimeError(
            "Admin hat bereits 2FA aktiviert – Tests benoetigen eine frische DB "
            "(alembic downgrade base && alembic upgrade head, API neu starten)."
        )
    secret = await _enable_2fa(client, data["access_token"])
    return await _login_with_2fa(client, "admin", ADMIN_PW, secret)
