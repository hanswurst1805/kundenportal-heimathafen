"""Kundenportal Heimathafen - FastAPI Hauptanwendung."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.auth import router as auth_router
from src.core.bootstrap import bootstrap_admin
from src.core.config import settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await bootstrap_admin()
    yield


app = FastAPI(
    title="Kundenportal Heimathafen",
    description="Anfrage, Angebot, Beauftragung, AVV, Leistungsschein, Status-Transparenz",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
