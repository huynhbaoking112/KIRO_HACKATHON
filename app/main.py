"""FastAPI application entry point."""

from contextlib import asynccontextmanager

import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.config.settings import get_settings
from app.infrastructure.database.mongodb import MongoDB
from app.infrastructure.redis.client import RedisClient
from app.socket_gateway import sio

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    await MongoDB.connect(settings.MONGODB_URI, settings.MONGODB_DB_NAME)
    await MongoDB.create_indexes()
    await RedisClient.connect(settings.REDIS_URL)
    yield
    # Shutdown
    await RedisClient.disconnect()
    await MongoDB.disconnect()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS middleware - allow frontend origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router, prefix=settings.API_V1_PREFIX)

# Combine FastAPI with Socket.IO for real-time messaging
# Socket.IO handles WebSocket connections at root path
# FastAPI handles REST API endpoints
combined_app = socketio.ASGIApp(sio, other_asgi_app=app)
