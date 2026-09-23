"""
Integration tests for FastAPI endpoints:
- GET  /api/v1/grid
- GET  /api/v1/grid/{zone_id}
- POST /api/v1/vehicles
- GET  /api/v1/vehicles
- GET  /api/v1/fl/metrics
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.grid.grid_service import init_grid_zones
from app.main import app


@pytest.fixture
def client_with_db() -> TestClient:
    """Create a test client with an in-memory SQLite database override."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    # Seed default zones into this memory db
    with TestingSession() as db:
        init_grid_zones(db, n=3)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_get_grid_zones_returns_seeded_zones(client_with_db: TestClient) -> None:
    """GET /api/v1/grid returns 9 zones with occupancy metrics."""
    response = client_with_db.get("/api/v1/grid")
    assert response.status_code == 200
    zones = response.json()
    assert len(zones) == 9
    assert any(z["zone_id"] == "zone_0_0" for z in zones)
    assert any(z["zone_id"] == "zone_1_1" for z in zones)
    assert all("occupancy_rate" in z for z in zones)


def test_get_single_zone_detail(client_with_db: TestClient) -> None:
    """GET /api/v1/grid/{zone_id} returns zone detail and recent readings list."""
    response = client_with_db.get("/api/v1/grid/zone_1_1")
    assert response.status_code == 200
    data = response.json()
    assert data["zone_id"] == "zone_1_1"
    assert "recent_readings" in data


def test_post_vehicle_reading_runs_inference_and_persists(client_with_db: TestClient) -> None:
    """POST /api/v1/vehicles predicts state and persists reading in DB."""
    # Stationary vehicle (0 speed, close beacon RSSI) -> expected parked
    payload = {
        "vehicle_id": "test_car_100",
        "lat": 18.5204,
        "lon": 73.8567,
        "gps_speed": 0.0,
        "ble_rssi": -55.0,
        "imu_magnitude": 0.01,
    }
    response = client_with_db.post("/api/v1/vehicles", json=payload)
    assert response.status_code == 201
    result = response.json()
    assert result["vehicle_id"] == "test_car_100"
    assert result["predicted_state"] in ("parked", "moving")
    assert result["zone_id"] is not None
    assert 0.0 <= result["confidence"] <= 1.0

    # Verify reading appears in GET /api/v1/vehicles
    get_resp = client_with_db.get("/api/v1/vehicles?vehicle_id=test_car_100")
    assert get_resp.status_code == 200
    readings = get_resp.json()
    assert len(readings) >= 1
    assert readings[0]["vehicle_id"] == "test_car_100"


def test_get_fl_metrics(client_with_db: TestClient) -> None:
    """GET /api/v1/fl/metrics returns FL experiment metrics."""
    response = client_with_db.get("/api/v1/fl/metrics")
    assert response.status_code == 200
    metrics = response.json()
    assert "experiment" in metrics
    assert "global_model_history" in metrics
    assert len(metrics["global_model_history"]) > 0
