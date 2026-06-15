from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.api.routes import (
    maintenance_route,
    safety_route,
    energy_route,
    production_route,
    chat_route,
    dashboard_route,
    reports_route,
    auth_route,
    demo_route,
)
from app.services.live_sensor import start_simulation, stop_simulation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Sherlock Backend starting up...")
    start_simulation()
    yield
    stop_simulation()
    logger.info("🛑 Sherlock Backend shutting down...")


app = FastAPI(
    title="Tata Steel Sherlock - Autonomous Plant Intelligence System",
    description="Multi-agent AI platform for industrial operations",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.include_router(auth_route.router,       prefix="/api/auth",       tags=["Auth"])
app.include_router(dashboard_route.router,  prefix="/api/dashboard",  tags=["Dashboard"])
app.include_router(maintenance_route.router,prefix="/api/maintenance",tags=["Maintenance"])
app.include_router(safety_route.router,     prefix="/api/safety",     tags=["Safety"])
app.include_router(energy_route.router,     prefix="/api/energy",     tags=["Energy"])
app.include_router(production_route.router, prefix="/api/production", tags=["Production"])
app.include_router(chat_route.router,       prefix="/api/chat",       tags=["AI Chat"])
app.include_router(reports_route.router,    prefix="/api/reports",    tags=["Reports"])
app.include_router(demo_route.router,       prefix="/api/demo",       tags=["Live Demo"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Sherlock Backend", "version": "1.0.0"}


@app.get("/")
async def root():
    return {
        "message": "Tata Steel Sherlock - Autonomous Plant Intelligence System",
        "docs": "/api/docs",
        "health": "/health",
    }
