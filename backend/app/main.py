from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.grid.grid_service import init_grid_zones
import app.db.models  # Registers ORM models with SQLAlchemy metadata.

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Create development tables and ensure the default Pune grid is seeded."""
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        init_grid_zones(db, n=settings.grid_n)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(api_router, prefix=settings.api_v1_prefix)

