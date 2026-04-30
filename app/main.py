import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.rate_limiter import limiter
from app.database import engine
from app.routers import router_auth, router_chat, router_friends


# Modern lifespan manager for FastAPI application lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown."""
    # Startup logic
    yield  # Server is running
    # Shutdown logic
    await engine.dispose()


app = FastAPI(title="Защищенный Чат-Сервер", lifespan=lifespan)

# Configure rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Setup static files
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    """Serve favicon."""
    favicon_path = os.path.join(STATIC_DIR, "favicon.ico")
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    from fastapi.responses import Response
    return Response(status_code=204)


# Register routers
app.include_router(router_auth.router)
app.include_router(router_friends.router)
app.include_router(router_chat.router)


if __name__ == "__main__":
    # Run database migrations before starting Uvicorn
    import logging
    from alembic.config import Config
    from alembic import command
    
    logging.info("Running database migrations...")
    try:
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        logging.info("Database migrations completed.")
    except Exception as e:
        logging.error(f"Failed to run migrations: {e}")
        sys.exit(1)

    # Start Uvicorn with configured host and port
    uvicorn.run("app.main:app", host=settings.host, port=settings.port)