from __future__ import annotations

from fastapi import APIRouter

from src.api.internal.anfragen import router as anfragen_router
from src.api.internal.angebote import router as angebote_router
from src.api.internal.auftraege import router as auftraege_router
from src.api.internal.avv import router as avv_router
from src.api.internal.avv import vorlagen_router as avv_vorlagen_router
from src.api.internal.bestellungen import router as bestellungen_router
from src.api.internal.kunden import router as kunden_router
from src.api.internal.leistungen import router as leistungen_router
from src.api.internal.leistungsscheine import router as leistungsscheine_router
from src.api.internal.monitoring import router as monitoring_router
from src.api.internal.signaturen import router as signaturen_router
from src.api.internal.statusregeln import router as statusregeln_router
from src.api.internal.umfragen import router as umfragen_router
from src.api.internal.users import router as users_router
from src.api.internal.workshops import router as workshops_router

router = APIRouter(prefix="/api/v1/intern")
router.include_router(anfragen_router)
router.include_router(angebote_router)
router.include_router(bestellungen_router)
router.include_router(auftraege_router)
router.include_router(leistungsscheine_router)
router.include_router(workshops_router)
router.include_router(avv_router)
router.include_router(avv_vorlagen_router)
router.include_router(signaturen_router)
router.include_router(monitoring_router)
router.include_router(kunden_router)
router.include_router(leistungen_router)
router.include_router(umfragen_router)
router.include_router(statusregeln_router)
router.include_router(users_router)
