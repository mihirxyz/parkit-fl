"""
Spatial grid service for the Pune parking area.

Partitions the SUMO dataset's real geographic extent:
    Latitude  18.5185 – 18.5222  (~411 m N–S)
    Longitude 73.8548 – 73.8586  (~378 m E–W)

into an NxN grid of ParkingZone records persisted in the SQLite database.
All zone state (occupancy, readings) survives process restarts.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import ParkingZone, VehicleReading

# ---------------------------------------------------------------------------
# Pune dataset bounds (from SUMO simulation / sumo_dataset.csv)
# ---------------------------------------------------------------------------
PUNE_BOUNDS: dict[str, float] = {
    "lat_min": 18.5185,
    "lat_max": 18.5222,
    "lon_min": 73.8548,
    "lon_max": 73.8586,
}

# Central cluster of zones that represent dedicated (structured) parking lots.
# For a 3x3 grid: NW lot (0,0), NE lot (0,2), and centre (1,1) are structured.
_STRUCTURED_CELLS: frozenset[tuple[int, int]] = frozenset({(0, 0), (0, 2), (1, 1)})

_ZONE_NAMES: dict[tuple[int, int], str] = {
    (0, 0): "North Lot",
    (0, 1): "North Curbside",
    (0, 2): "East Lot",
    (1, 0): "West Roadside",
    (1, 1): "Central Lot",
    (1, 2): "East Roadside",
    (2, 0): "South Roadside West",
    (2, 1): "South Curbside",
    (2, 2): "South Roadside East",
}



# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _zone_type(row: int, col: int) -> str:
    return "structured" if (row, col) in _STRUCTURED_CELLS else "unstructured"


def init_grid_zones(
    db: Session, n: int = 3, force_reset: bool = False
) -> list[ParkingZone]:
    """Ensure the NxN Pune parking-zone grid exists in the database.

    Idempotent: returns existing rows unless *force_reset* is True.
    """
    existing = db.scalars(select(ParkingZone)).all()
    if existing and not force_reset:
        return list(existing)

    if force_reset:
        for zone in existing:
            db.delete(zone)
        db.commit()

    lat_step = (PUNE_BOUNDS["lat_max"] - PUNE_BOUNDS["lat_min"]) / n
    lon_step = (PUNE_BOUNDS["lon_max"] - PUNE_BOUNDS["lon_min"]) / n

    zones: list[ParkingZone] = []
    for row in range(n):
        for col in range(n):
            zt = _zone_type(row, col)
            zone = ParkingZone(
                zone_id=f"zone_{row}_{col}",
                lat_min=round(PUNE_BOUNDS["lat_min"] + row * lat_step, 7),
                lat_max=round(PUNE_BOUNDS["lat_min"] + (row + 1) * lat_step, 7),
                lon_min=round(PUNE_BOUNDS["lon_min"] + col * lon_step, 7),
                lon_max=round(PUNE_BOUNDS["lon_min"] + (col + 1) * lon_step, 7),
                zone_type=zt,
                name=_ZONE_NAMES.get((row, col), f"Zone ({row},{col})"),
                total_capacity=15 if zt == "structured" else 8,
            )
            zones.append(zone)
            db.add(zone)

    db.commit()
    for z in zones:
        db.refresh(z)
    return zones


def find_zone_for_coordinates(
    db: Session, lat: float, lon: float
) -> Optional[ParkingZone]:
    """Return the ParkingZone whose bounding box contains (lat, lon), or None."""
    stmt = (
        select(ParkingZone)
        .where(ParkingZone.lat_min <= lat)
        .where(ParkingZone.lat_max > lat)
        .where(ParkingZone.lon_min <= lon)
        .where(ParkingZone.lon_max > lon)
        .limit(1)
    )
    zone = db.scalars(stmt).first()
    if zone is not None:
        return zone

    # Clamp: handle points exactly on the outer upper boundary.
    stmt_clamp = (
        select(ParkingZone)
        .where(ParkingZone.lat_min <= lat)
        .where(ParkingZone.lat_max >= lat)
        .where(ParkingZone.lon_min <= lon)
        .where(ParkingZone.lon_max >= lon)
        .limit(1)
    )
    return db.scalars(stmt_clamp).first()


def get_zone_statuses(db: Session) -> list[dict]:
    """Return all zones enriched with real-time occupancy counts.

    Occupancy is derived from the most-recent VehicleReading per unique
    vehicle_id in each zone (latest wins).
    """
    zones = db.scalars(select(ParkingZone).order_by(ParkingZone.zone_id)).all()

    # Subquery: max reading id per vehicle_id
    latest_sub = (
        select(
            VehicleReading.vehicle_id,
            func.max(VehicleReading.id).label("max_id"),
        )
        .group_by(VehicleReading.vehicle_id)
        .subquery()
    )

    latest_readings = db.scalars(
        select(VehicleReading).join(
            latest_sub,
            VehicleReading.id == latest_sub.c.max_id,
        )
    ).all()

    by_zone: dict[str, list[VehicleReading]] = {}
    for r in latest_readings:
        if r.zone_id:
            by_zone.setdefault(r.zone_id, []).append(r)

    statuses = []
    for zone in zones:
        in_zone = by_zone.get(zone.zone_id, [])
        parked = sum(1 for r in in_zone if r.predicted_state == "parked")
        moving = len(in_zone) - parked
        cap = zone.total_capacity or 1
        statuses.append(
            {
                "zone_id": zone.zone_id,
                "name": zone.name,
                "zone_type": zone.zone_type,
                "lat_min": zone.lat_min,
                "lat_max": zone.lat_max,
                "lon_min": zone.lon_min,
                "lon_max": zone.lon_max,
                "total_capacity": zone.total_capacity,
                "parked_vehicles": parked,
                "moving_vehicles": moving,
                "total_vehicles": len(in_zone),
                "occupancy_rate": round(parked / cap, 4),
            }
        )
    return statuses

    return zones



def record_vehicle_reading(
    db: Session,
    *,
    vehicle_id: str,
    lat: float,
    lon: float,
    predicted_state: str,
    confidence: float,
    gps_speed: Optional[float] = None,
    ble_rssi: Optional[float] = None,
    imu_magnitude: Optional[float] = None,
    timestamp: Optional[datetime] = None,
) -> VehicleReading:
    """Persist a VehicleReading, resolving the matching zone from the DB.

    Returns the persisted ORM instance with an assigned primary key.
    """
    zone = find_zone_for_coordinates(db, lat, lon)
    reading = VehicleReading(
        vehicle_id=vehicle_id,
        lat=lat,
        lon=lon,
        predicted_state=predicted_state,
        zone_id=zone.zone_id if zone else None,
        confidence=confidence,
        gps_speed=gps_speed,
        ble_rssi=ble_rssi,
        imu_magnitude=imu_magnitude,
        timestamp=timestamp or datetime.now(tz=timezone.utc),
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)
    return reading
