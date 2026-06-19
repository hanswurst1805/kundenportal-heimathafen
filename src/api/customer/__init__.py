from __future__ import annotations

from fastapi import APIRouter

from src.api.customer.anfragen import router as anfragen_router
from src.api.customer.angebote import router as angebote_router
from src.api.customer.auftraege import router as auftraege_router
from src.api.customer.avv import router as avv_router
from src.api.customer.bestellungen import router as bestellungen_router
from src.api.customer.catalog import router as catalog_router
from src.api.customer.dashboard import router as dashboard_router
from src.api.customer.dokumente import router as dokumente_router
from src.api.customer.leistungsscheine import router as leistungsscheine_router
from src.api.customer.signatur import router as signatur_router
from src.api.customer.umfragen import router as umfragen_router
from src.api.customer.vorgaenge import router as vorgaenge_router

router = APIRouter(prefix="/api/v1/portal")
router.include_router(dashboard_router)
router.include_router(vorgaenge_router)
router.include_router(catalog_router)
router.include_router(bestellungen_router)
router.include_router(anfragen_router)
router.include_router(angebote_router)
router.include_router(signatur_router)
router.include_router(avv_router)
router.include_router(auftraege_router)
router.include_router(leistungsscheine_router)
router.include_router(dokumente_router)
router.include_router(umfragen_router)
