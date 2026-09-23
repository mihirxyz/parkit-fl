"""
Unit and concurrency tests for Federated Learning Coordinator (fl_server.py).
"""

import concurrent.futures
import pytest
from fastapi.testclient import TestClient

from app.ml.fl_server import app, server, FLServer


@pytest.fixture(autouse=True)
def reset_server():
    """Reset the FL server state before each test."""
    global server
    server.__init__(num_clients=5)


def test_health_endpoint():
    """Test health check endpoint."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["current_round"] == 0


def test_client_registration():
    """Test registering clients via both /register and /register_client."""
    client = TestClient(app)
    
    # Test /register_client
    resp = client.post("/register_client", json={"client_id": "client_0", "num_samples": 100})
    assert resp.status_code == 200
    assert resp.json()["status"] == "registered"
    
    # Test duplicate registration
    resp = client.post("/register_client", json={"client_id": "client_0", "num_samples": 100})
    assert resp.status_code == 200
    assert resp.json()["status"] == "already_registered"
    
    # Test /register alias
    resp = client.post("/register", json={"client_id": "client_1", "num_samples": 150})
    assert resp.status_code == 200
    assert resp.json()["status"] == "registered"


def test_global_model_endpoint():
    """Test getting global model weights."""
    client = TestClient(app)
    resp = client.get("/global_model")
    assert resp.status_code == 200
    weights = resp.json()
    assert isinstance(weights, dict)
    assert len(weights) > 0
    # Check that keys match model parameters
    for key in ["fc1.weight", "fc1.bias", "fc2.weight", "fc2.bias"]:
        assert key in weights


def test_concurrent_registrations():
    """Test 5 concurrent client registrations."""
    client = TestClient(app)
    
    def register(i):
        return client.post(
            "/register_client",
            json={"client_id": f"client_{i}", "num_samples": 100 * (i + 1)},
        )
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(register, i) for i in range(5)]
        responses = [f.result() for f in futures]
    
    for resp in responses:
        assert resp.status_code == 200
        assert resp.json()["status"] == "registered"
    
    assert len(server.clients) == 5


def test_full_round_aggregation():
    """Test round update submissions and synchronous FedAvg aggregation."""
    client = TestClient(app)
    
    # Register 5 clients
    for i in range(5):
        client.post("/register_client", json={"client_id": f"client_{i}", "num_samples": 100})
    
    # Get initial model weights
    init_weights = client.get("/global_model").json()
    
    # Submit updates concurrently for round 0
    def submit(i):
        # Slightly alter weights for client update
        client_weights = {k: v for k, v in init_weights.items()}
        return client.post(
            "/submit_update",
            json={
                "client_id": f"client_{i}",
                "round_num": 0,
                "weights": client_weights,
                "num_samples": 100,
                "local_loss": 0.5,
            },
        )
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(submit, i) for i in range(5)]
        responses = [f.result() for f in futures]
    
    for resp in responses:
        assert resp.status_code == 200
        assert resp.json()["status"] == "accepted"
    
    # Server should have aggregated round 0 and advanced to round 1
    assert server.current_round == 1
    assert len(server.round_history) == 1
    assert server.round_history[0]["round"] == 0
    assert server.round_history[0]["clients_participated"] == 5
    
    # Test round status for completed round 0
    status_r0 = client.get("/round_status", params={"round_num": 0}).json()
    assert status_r0["round_complete"] is True
    assert status_r0["current_round"] == 1
    
    # Test round status for active round 1
    status_r1 = client.get("/round_status", params={"round_num": 1}).json()
    assert status_r1["round_complete"] is False
    assert status_r1["clients_participated"] == 0
