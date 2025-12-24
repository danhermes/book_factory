"""Book Agent - FastAPI Application."""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import STATIC_DIR

# Track background tasks for cleanup
background_tasks_set: set = set()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown."""
    # Startup
    print("Book Agent starting...")
    yield
    # Shutdown
    print("Cancelling background tasks...")
    for task in background_tasks_set:
        task.cancel()
    if background_tasks_set:
        await asyncio.gather(*background_tasks_set, return_exceptions=True)
    background_tasks_set.clear()
    print("Shutdown complete.")


# Create app
app = FastAPI(title="Book Agent Editor", lifespan=lifespan)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Import and include routes
from .routes import router
app.include_router(router)
