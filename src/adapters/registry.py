"""Factory-Registry fuer austauschbare Adapter (Default: 'stub')."""

from __future__ import annotations

from functools import lru_cache

from src.adapters.avv.base import AVVWorkflow
from src.adapters.avv.stub import StubAVVWorkflow
from src.adapters.notification.base import NotificationProvider
from src.adapters.notification.stub import StubNotificationProvider
from src.adapters.signature.base import SignatureProvider
from src.adapters.signature.inhouse import InhouseSignatureProvider
from src.adapters.signature.stub import StubSignatureProvider
from src.adapters.target_system.base import TargetSystemAdapter
from src.adapters.target_system.stub import StubTargetSystemAdapter
from src.core.config import settings


@lru_cache
def get_signature_provider_by_name(name: str) -> SignatureProvider:
    """Provider anhand seines Namens (z. B. ``vorgang.anbieter``) – damit ein
    Vorgang konsistent bleibt, auch wenn die globale Einstellung wechselt."""
    if name == "stub":
        return StubSignatureProvider()
    if name == "inhouse":
        return InhouseSignatureProvider()
    raise ValueError(f"Unbekannter signature-Anbieter: {name}")


def get_signature_provider() -> SignatureProvider:
    return get_signature_provider_by_name(settings.signature_provider)


@lru_cache
def get_avv_workflow() -> AVVWorkflow:
    if settings.avv_provider == "stub":
        return StubAVVWorkflow(get_signature_provider())
    raise ValueError(f"Unbekannter avv_provider: {settings.avv_provider}")


@lru_cache
def get_target_system_adapter() -> TargetSystemAdapter:
    if settings.target_system_provider == "stub":
        return StubTargetSystemAdapter()
    raise ValueError(f"Unbekannter target_system_provider: {settings.target_system_provider}")


@lru_cache
def get_notification_provider() -> NotificationProvider:
    if settings.notification_provider == "stub":
        return StubNotificationProvider()
    raise ValueError(f"Unbekannter notification_provider: {settings.notification_provider}")
