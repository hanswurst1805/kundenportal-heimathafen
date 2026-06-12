"""Schnittstelle fuer den Benachrichtigungsversand (z.B. E-Mail)."""

from __future__ import annotations

from typing import Protocol


class NotificationProvider(Protocol):
    async def send_email(self, to: str, subject: str, body: str) -> None:
        ...
