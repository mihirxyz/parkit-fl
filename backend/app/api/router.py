from fastapi import APIRouter

from app.api.routes.fl import router as fl_router
from app.api.routes.grid import router as grid_router
from app.api.routes.health import router as health_router
from app.api.routes.vehicles import router as vehicles_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(grid_router)
api_router.include_router(vehicles_router)
api_router.include_router(fl_router)

