"""
Grid router – zone status and initialisation endpoints.

Routes (all under /api/v1/grid):
    GET  /           – list all zones with live occupancy
    GET  /{zone_id}  – single-zone detail + recent readings
    POST /init       – (re-)initialise the NxN grid
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ParkingZone, VehicleReading
from app.db.session import get_db
from app.grid.grid_service import get_zone_statuses, init_grid_zones

router = APIRouter(prefix="/grid", tags=["grid"])


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class ZoneStatus(BaseModel):
    zone_id: str
    name: str | None
    zone_type: str
    lat_min: float
    lat_max: float
    lon_min: float
    lon_max: float
    total_capacity: int
    parked_vehicles: int
    moving_vehicles: int
    total_vehicles: int
    occupancy_rate: float

    model_config = {"from_attributes": True}


class ZoneDetail(ZoneStatus):
    recent_readings: list[dict[str, Any]] = []


class GridInitRequest(BaseModel):
    n: int = 3
    force_reset: bool = False


class GridInitResponse(BaseModel):
    zones_created: int
    n: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("", response_model=list[ZoneStatus], status_code=status.HTTP_200_OK)
def list_zones(db: Session = Depends(get_db)) -> list[ZoneStatus]:
    """Return all parking zones with real-time occupancy counts."""
    statuses = get_zone_statuses(db)
    return [ZoneStatus(**s) for s in statuses]


@router.get("/{zone_id}", response_model=ZoneDetail, status_code=status.HTTP_200_OK)
def get_zone(
    zone_id: str,
    limit: int = Query(20, ge=1, le=100, description="Max recent readings to return"),
    db: Session = Depends(get_db),
) -> ZoneDetail:
    """Return detail for a single zone including the most recent readings."""
    zone = db.get(ParkingZone, zone_id)
    if zone is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Zone '{zone_id}' not found.",
        )

    # Aggregate occupancy counts for this zone
    statuses = {s["zone_id"]: s for s in get_zone_statuses(db)}
    zone_status = statuses.get(zone_id, {})

    # Fetch N most-recent readings
    recent = db.scalars(
        select(VehicleReading)
        .where(VehicleReading.zone_id == zone_id)
        .order_by(VehicleReading.id.desc())
        .limit(limit)
    ).all()

    readings_out = [
        {
            "id": r.id,
            "vehicle_id": r.vehicle_id,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            "lat": r.lat,
            "lon": r.lon,
            "predicted_state": r.predicted_state,
            "confidence": r.confidence,
            "gps_speed": r.gps_speed,
            "ble_rssi": r.ble_rssi,
            "imu_magnitude": r.imu_magnitude,
        }
        for r in recent
    ]

    return ZoneDetail(
        zone_id=zone.zone_id,
        name=zone.name,
        zone_type=zone.zone_type,
        lat_min=zone.lat_min,
        lat_max=zone.lat_max,
        lon_min=zone.lon_min,
        lon_max=zone.lon_max,
        total_capacity=zone.total_capacity,
        parked_vehicles=zone_status.get("parked_vehicles", 0),
        moving_vehicles=zone_status.get("moving_vehicles", 0),
        total_vehicles=zone_status.get("total_vehicles", 0),
        occupancy_rate=zone_status.get("occupancy_rate", 0.0),
        recent_readings=readings_out,
    )


@router.post("/init", response_model=GridInitResponse, status_code=status.HTTP_200_OK)
def initialise_grid(
    body: GridInitRequest, db: Session = Depends(get_db)
) -> GridInitResponse:
    """(Re-)initialise the Pune NxN parking-zone grid in the database."""
    if not (1 <= body.n <= 10):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="n must be between 1 and 10.",
        )
    zones = init_grid_zones(db, n=body.n, force_reset=body.force_reset)
    return GridInitResponse(zones_created=len(zones), n=body.n)
