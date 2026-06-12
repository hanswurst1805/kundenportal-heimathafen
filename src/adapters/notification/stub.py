"""Stub-Implementierung: loggt Benachrichtigungen statt sie zu versenden."""

from __future__ import annotations

import logging

logger = logging.getLogger("notifications")


class StubNotificationProvider:
    async def send_email(self, to: str, subject: str, body: str) -> None:
        logger.info("E-Mail (stub) an %s: %s\n%s", to, subject, body)
