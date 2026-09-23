"""
Vehicles router – ingest sensor readings, run ML inference, persist results.

Routes (all under /api/v1/vehicles):
    POST /          – submit a new vehicle telemetry reading
    GET  /          – list recent readings (filterable)
    GET  /{id}      – single reading detail
"""

from __future__ import annotations

import random
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Optional

import torch
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import VehicleReading
from app.db.session import get_db
from app.grid.grid_service import record_vehicle_reading
from app.ml.model import ParkingStateClassifier
from app.simulation.sensors import derive_ble_rssi, derive_gps_speed, derive_imu_magnitude

router = APIRouter(prefix="/vehicles", tags=["vehicles"])

_MODEL_WEIGHTS = Path(__file__).resolve().parent.parent.parent / "ml" / "model_weights.pth"


# ---------------------------------------------------------------------------
# Singleton model loader (loaded once, reused across requests)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _get_model() -> ParkingStateClassifier:
    """Load and cache the trained ParkingStateClassifier."""
    model = ParkingStateClassifier()
    if _MODEL_WEIGHTS.exists():
        state = torch.load(_MODEL_WEIGHTS, map_location=torch.device("cpu"), weights_only=True)
        model.load_state_dict(state)
    model.eval()
    return model


def _predict(gps_speed: float, ble_rssi: float, imu_magnitude: float) -> tuple[str, float]:
    """Run a single inference. Returns (predicted_state, confidence)."""
    model = _get_model()
    x = torch.tensor([[gps_speed, ble_rssi, imu_magnitude]], dtype=torch.float32)
    with torch.no_grad():
        prob: float = torch.sigmoid(model(x)).item()
    state = "parked" if prob >= 0.5 else "moving"
    confidence = prob if state == "parked" else 1.0 - prob
    return state, round(confidence, 6)



# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class VehicleReadingCreate(BaseModel):
    vehicle_id: str = Field(..., min_length=1, max_length=64)
    lat: float = Field(..., ge=-90.0, le=90.0)
    lon: float = Field(..., ge=-180.0, le=180.0)
    gps_speed: Optional[float] = Field(None, ge=0.0)
    ble_rssi: Optional[float] = Field(None, le=0.0)
    imu_magnitude: Optional[float] = Field(None, ge=0.0)
    timestamp: Optional[datetime] = None


class VehicleReadingResponse(BaseModel):
    id: int
    vehicle_id: str
    timestamp: datetime
    lat: float
    lon: float
    predicted_state: str
    confidence: float
    zone_id: Optional[str]
    gps_speed: Optional[float]
    ble_rssi: Optional[float]
    imu_magnitude: Optional[float]

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("", response_model=VehicleReadingResponse, status_code=status.HTTP_201_CREATED)
def submit_reading(
    body: VehicleReadingCreate, db: Session = Depends(get_db)
) -> VehicleReadingResponse:
    """Ingest a vehicle telemetry reading with ML-based state prediction."""
    rng = random.Random()
    speed_mps = body.gps_speed if body.gps_speed is not None else 0.0
    gps_speed = body.gps_speed if body.gps_speed is not None else derive_gps_speed(speed_mps, rng)
    ble_rssi = body.ble_rssi if body.ble_rssi is not None else derive_ble_rssi(15.0, rng)
    imu_magnitude = (
        body.imu_magnitude if body.imu_magnitude is not None
        else derive_imu_magnitude(speed_mps, 0.0, 1.0, rng)
    )

    predicted_state, confidence = _predict(gps_speed, ble_rssi, imu_magnitude)

    reading = record_vehicle_reading(
        db,
        vehicle_id=body.vehicle_id,
        lat=body.lat,
        lon=body.lon,
        predicted_state=predicted_state,
        confidence=confidence,
        gps_speed=gps_speed,
        ble_rssi=ble_rssi,
        imu_magnitude=imu_magnitude,
        timestamp=body.timestamp or datetime.now(tz=timezone.utc),
    )
    return VehicleReadingResponse.model_validate(reading)


@router.get("", response_model=list[VehicleReadingResponse])
def list_readings(
    zone_id: Optional[str] = Query(None),
    vehicle_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[VehicleReadingResponse]:
    """Return recent vehicle readings, newest first."""
    stmt = select(VehicleReading).order_by(VehicleReading.id.desc()).limit(limit)
    if zone_id:
        stmt = stmt.where(VehicleReading.zone_id == zone_id)
    if vehicle_id:
        stmt = stmt.where(VehicleReading.vehicle_id == vehicle_id)
    rows = db.scalars(stmt).all()
    return [VehicleReadingResponse.model_validate(r) for r in rows]


@router.get("/{reading_id}", response_model=VehicleReadingResponse)
def get_reading(reading_id: int, db: Session = Depends(get_db)) -> VehicleReadingResponse:
    """Return a single vehicle reading by its database ID."""
    row = db.get(VehicleReading, reading_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Reading {reading_id} not found.")
    return VehicleReadingResponse.model_validate(row)

