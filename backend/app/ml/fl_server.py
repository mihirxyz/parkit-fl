#!/usr/bin/env python3
"""
Federated Learning Server (FL Coordinator)

FastAPI-based server that:
- Registers clients
- Serves global model weights
- Receives local model updates from clients
- Aggregates updates using FedAvg
- Tracks round progress

Design principle: Simple, correct concurrency with a single lock protecting all shared state.
No background threads, no complex synchronization, no timeouts on locks.
"""

import json
import logging
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import torch
import torch.nn as nn
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Setup logging to both console and file
LOG_DIR = Path(__file__).resolve().parent / "results"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "fl_server.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("fl_server")

# Import model
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from app.ml.model import ParkingStateClassifier


# ============================================================================
# Data Models
# ============================================================================

class RegisterClientRequest(BaseModel):
    """Client registration request."""
    client_id: str
    num_samples: int


class RegisterClientResponse(BaseModel):
    """Client registration response."""
    client_id: str
    status: str


class SubmitUpdateRequest(BaseModel):
    """Client weight submission."""
    client_id: str
    round_num: int
    weights: Dict[str, Union[List[float], List[List[float]]]]
    num_samples: int
    local_loss: Optional[float] = None


class SubmitUpdateResponse(BaseModel):
    """Update submission response."""
    round_num: int
    status: str


class RoundStatusResponse(BaseModel):
    """Round status info."""
    current_round: int
    round_complete: bool
    clients_participated: int
    clients_total: int


# ============================================================================
# Federated Learning Server
# ============================================================================

class FLServer:
    """Federated Learning Coordinator with simple, correct concurrency."""
    
    def __init__(self, num_clients: int = 5):
        """Initialize server."""
        self.num_clients = num_clients
        self.current_round = 0
        
        # Global model (initialized randomly)
        self.global_model = ParkingStateClassifier()
        self.global_weights = self._serialize_weights(self.global_model.state_dict())
        
        # Client registry: client_id -> num_samples
        self.clients: Dict[str, int] = {}
        
        # Round tracking: current_round -> {client_id -> (weights, num_samples)}
        self.round_updates: Dict[int, Dict[str, Tuple[Dict, int]]] = {}
        
        # History for logging
        self.round_history: List[Dict] = []
        
        # SINGLE LOCK protecting ALL shared state
        self.lock = threading.Lock()
        
        logger.info(f"FL Server initialized for {num_clients} clients")
    
    def _serialize_weights(self, state_dict: dict) -> dict:
        """Convert torch state dict to serializable format."""
        serialized = {}
        for k, v in state_dict.items():
            if isinstance(v, torch.Tensor):
                serialized[k] = v.detach().cpu().numpy().tolist()
            else:
                serialized[k] = v
        return serialized
    
    def _deserialize_weights(self, weights: dict) -> dict:
        """Convert serialized weights back to numpy format."""
        deserialized = {}
        for k, v in weights.items():
            if isinstance(v, list):
                deserialized[k] = np.array(v, dtype=np.float32)
            else:
                deserialized[k] = v
        return deserialized
    
    def register_client(self, client_id: str, num_samples: int) -> RegisterClientResponse:
        """Register a client."""
        with self.lock:
            if client_id in self.clients:
                return RegisterClientResponse(client_id=client_id, status="already_registered")
            
            self.clients[client_id] = num_samples
            logger.info(f"Client {client_id} registered ({len(self.clients)}/{self.num_clients} registered)")
            return RegisterClientResponse(client_id=client_id, status="registered")
    
    def get_global_weights(self) -> dict:
        """Get current global model weights (serialized dictionary)."""
        with self.lock:
            return self.global_weights
    
    def get_global_model(self) -> dict:
        """Alias for get_global_weights."""
        return self.get_global_weights()
    
    def submit_update(
        self,
        client_id: str,
        round_num: int,
        weights: dict,
        num_samples: int,
        local_loss: Optional[float] = None,
    ) -> SubmitUpdateResponse:
        """
        Accept local model update from client.
        If this is the last client to submit for the round, aggregate immediately.
        """
        with self.lock:
            # Validate client and round
            if client_id not in self.clients:
                raise HTTPException(status_code=400, detail=f"Client {client_id} not registered")
            
            if round_num != self.current_round:
                raise HTTPException(
                    status_code=400,
                    detail=f"Expected round {self.current_round}, got {round_num}",
                )
            
            # Initialize round updates dict if needed
            if round_num not in self.round_updates:
                self.round_updates[round_num] = {}
            
            # Store this client's update
            self.round_updates[round_num][client_id] = (weights, num_samples)
            
            num_received = len(self.round_updates[round_num])
            logger.info(f"Update received from {client_id} for round {round_num}: {num_received}/{self.num_clients} clients")
            
            # If all clients have submitted, aggregate immediately
            if num_received == self.num_clients:
                self._aggregate_round_locked(round_num)
            
            return SubmitUpdateResponse(round_num=round_num, status="accepted")
    
    def _aggregate_round_locked(self, round_num: int) -> None:
        """
        Perform FedAvg aggregation: w_global = sum(n_i / n_total * w_i)
        
        Called while holding self.lock. Advances to next round when complete.
        """
        if round_num not in self.round_updates:
            logger.error(f"Round {round_num} has no updates, skipping aggregation")
            return
        
        updates = self.round_updates[round_num]
        if len(updates) == 0:
            logger.error(f"Round {round_num} updates dict is empty, skipping aggregation")
            return
        
        total_samples = sum(num_samples for _, num_samples in updates.values())
        
        # Perform FedAvg aggregation
        aggregated = None
        for client_id, (weights, num_samples) in updates.items():
            weight = num_samples / total_samples
            deserialized = self._deserialize_weights(weights)
            
            if aggregated is None:
                aggregated = {k: weight * v for k, v in deserialized.items()}
            else:
                for k, v in deserialized.items():
                    aggregated[k] = aggregated[k] + weight * v
        
        # Convert aggregated weights to torch tensors
        state_dict = {}
        for k, v in aggregated.items():
            if isinstance(v, np.ndarray):
                state_dict[k] = torch.tensor(v, dtype=torch.float32)
            elif isinstance(v, list):
                state_dict[k] = torch.tensor(v, dtype=torch.float32)
            else:
                state_dict[k] = v
        
        # Load into global model and serialize
        self.global_model.load_state_dict(state_dict)
        self.global_weights = self._serialize_weights(state_dict)
        
        # Record history
        self.round_history.append({
            "round": round_num,
            "clients_participated": len(updates),
            "total_samples": total_samples,
        })
        
        # Advance to next round
        self.current_round = round_num + 1
        logger.info(f"Round {round_num} aggregated. Advancing to round {self.current_round}")
    
    def get_round_status(self, round_num: Optional[int] = None) -> RoundStatusResponse:
        """Get round status. If round_num is provided, check status for that specific round."""
        with self.lock:
            if round_num is not None:
                if round_num < self.current_round:
                    return RoundStatusResponse(
                        current_round=self.current_round,
                        round_complete=True,
                        clients_participated=self.num_clients,
                        clients_total=self.num_clients,
                    )
                target_round = round_num
            else:
                target_round = self.current_round
            
            if target_round not in self.round_updates:
                clients_participated = 0
            else:
                clients_participated = len(self.round_updates[target_round])
            
            round_complete = clients_participated == self.num_clients
            
            return RoundStatusResponse(
                current_round=self.current_round,
                round_complete=round_complete,
                clients_participated=clients_participated,
                clients_total=self.num_clients,
            )


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(title="Federated Learning Server")
server = FLServer(num_clients=5)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Handle validation errors."""
    logger.error(f"Validation error: {exc}")
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok", "current_round": server.current_round}


@app.post("/register_client", response_model=RegisterClientResponse)
@app.post("/register", response_model=RegisterClientResponse)
def register_client(request: RegisterClientRequest):
    """Register a client for federated learning."""
    try:
        response = server.register_client(request.client_id, request.num_samples)
        return response
    except Exception as e:
        logger.error(f"Error in registration: {e}", exc_info=True)
        raise


@app.get("/global_model")
def get_global_model():
    """Get current global model weights dictionary."""
    try:
        return server.get_global_weights()
    except Exception as e:
        logger.error(f"Error in /global_model: {e}", exc_info=True)
        raise


@app.post("/submit_update", response_model=SubmitUpdateResponse)
def submit_update(request: SubmitUpdateRequest):
    """Submit local model update from client."""
    try:
        response = server.submit_update(
            request.client_id,
            request.round_num,
            request.weights,
            request.num_samples,
            request.local_loss,
        )
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in /submit_update: {e}", exc_info=True)
        raise


@app.get("/round_status", response_model=RoundStatusResponse)
def get_round_status(round_num: Optional[int] = None):
    """Get current round status."""
    try:
        status = server.get_round_status(round_num=round_num)
        return status
    except Exception as e:
        logger.error(f"Error in /round_status: {e}", exc_info=True)
        raise


@app.get("/history")
def get_history():
    """Get aggregation history."""
    try:
        with server.lock:
            return {
                "current_round": server.current_round,
                "history": server.round_history,
            }
    except Exception as e:
        logger.error(f"Error in /history: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")


