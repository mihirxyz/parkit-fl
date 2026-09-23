from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine
import app.db.models  # Registers ORM models with SQLAlchemy metadata.

settings = get_settings()
app = FastAPI(title=settings.app_name)
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.on_event("startup")
def create_database_tables() -> None:
    """Create development tables; production deployments should use migrations."""
    Base.metadata.create_all(bind=engine)
