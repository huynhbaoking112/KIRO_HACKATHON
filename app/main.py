"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import router as v1_router
from app.config.settings import get_settings
from app.infrastructure.database.mongodb import MongoDB

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    await MongoDB.connect(settings.MONGODB_URI, settings.MONGODB_DB_NAME)
    yield
    # Shutdown
    await MongoDB.disconnect()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.include_router(v1_router, prefix=settings.API_V1_PREFIX)
