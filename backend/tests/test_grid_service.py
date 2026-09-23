"""
Unit tests for the spatial grid partitioning service and database operations.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.models import ParkingZone, VehicleReading
from app.grid.grid_service import (
    PUNE_BOUNDS,
    find_zone_for_coordinates,
    get_zone_statuses,
    init_grid_zones,
    record_vehicle_reading,
)


@pytest.fixture
def db_session() -> Session:
    """Create an isolated in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_init_grid_zones_creates_nxn_zones(db_session: Session) -> None:
    """Ensure init_grid_zones creates 9 zones for n=3 and is idempotent."""
    zones = init_grid_zones(db_session, n=3)
    assert len(zones) == 9

    # Re-running without force_reset should return existing zones without error
    zones_again = init_grid_zones(db_session, n=3)
    assert len(zones_again) == 9

    # Verify coverage covers Pune bounds
    all_lat_min = min(z.lat_min for z in zones)
    all_lat_max = max(z.lat_max for z in zones)
    all_lon_min = min(z.lon_min for z in zones)
    all_lon_max = max(z.lon_max for z in zones)

    assert pytest.approx(all_lat_min, abs=1e-4) == PUNE_BOUNDS["lat_min"]
    assert pytest.approx(all_lat_max, abs=1e-4) == PUNE_BOUNDS["lat_max"]
    assert pytest.approx(all_lon_min, abs=1e-4) == PUNE_BOUNDS["lon_min"]
    assert pytest.approx(all_lon_max, abs=1e-4) == PUNE_BOUNDS["lon_max"]


def test_find_zone_for_coordinates_identifies_correct_cell(db_session: Session) -> None:
    """Ensure coordinates inside Pune bounds are matched to correct zone."""
    init_grid_zones(db_session, n=3)

    # North-West point (should map to row 0, col 0)
    lat_nw = PUNE_BOUNDS["lat_min"] + 0.0002
    lon_nw = PUNE_BOUNDS["lon_min"] + 0.0002
    zone_nw = find_zone_for_coordinates(db_session, lat_nw, lon_nw)
    assert zone_nw is not None
    assert zone_nw.zone_id == "zone_0_0"

    # Center point (should map to row 1, col 1)
    lat_center = (PUNE_BOUNDS["lat_min"] + PUNE_BOUNDS["lat_max"]) / 2.0
    lon_center = (PUNE_BOUNDS["lon_min"] + PUNE_BOUNDS["lon_max"]) / 2.0
    zone_center = find_zone_for_coordinates(db_session, lat_center, lon_center)
    assert zone_center is not None
    assert zone_center.zone_id == "zone_1_1"


def test_record_vehicle_reading_persists_and_associates_zone(db_session: Session) -> None:
    """Test persisting vehicle readings and updating occupancy statuses."""
    init_grid_zones(db_session, n=3)

    lat_c = (PUNE_BOUNDS["lat_min"] + PUNE_BOUNDS["lat_max"]) / 2.0
    lon_c = (PUNE_BOUNDS["lon_min"] + PUNE_BOUNDS["lon_max"]) / 2.0

    reading1 = record_vehicle_reading(
        db_session,
        vehicle_id="veh_001",
        lat=lat_c,
        lon=lon_c,
        predicted_state="parked",
        confidence=0.98,
        gps_speed=0.0,
        ble_rssi=-82.0,
        imu_magnitude=0.02,
    )
    assert reading1.id is not None
    assert reading1.zone_id == "zone_1_1"
    assert reading1.predicted_state == "parked"

    reading2 = record_vehicle_reading(
        db_session,
        vehicle_id="veh_002",
        lat=lat_c,
        lon=lon_c,
        predicted_state="moving",
        confidence=0.95,
        gps_speed=8.5,
        ble_rssi=-90.0,
        imu_magnitude=0.15,
    )
    assert reading2.zone_id == "zone_1_1"

    statuses = get_zone_statuses(db_session)
    zone_1_1_status = next(s for s in statuses if s["zone_id"] == "zone_1_1")
    assert zone_1_1_status["parked_vehicles"] == 1
    assert zone_1_1_status["moving_vehicles"] == 1
    assert zone_1_1_status["total_vehicles"] == 2
