#!/usr/bin/env python3
"""
Federated Learning Client

Standalone client script that:
- Loads data partition (by vehicle_id range)
- Registers with FL server
- Downloads global model
- Trains locally
- Uploads updated weights
- Repeats for N rounds
"""

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
import requests
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("fl_client")

# Add backend to path
root_dir = Path(__file__).resolve().parent.parent  # parkit-fl/
backend_dir = root_dir / "backend"
sys.path.insert(0, str(backend_dir))

from app.ml.model import ParkingStateClassifier


# ============================================================================
# Configuration
# ============================================================================

BATCH_SIZE = 32
LEARNING_RATE = 0.001
LOCAL_EPOCHS = 3
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# ============================================================================
# Data Loading & Partitioning
# ============================================================================

def load_and_partition_data(
    csv_path: Path, client_id: int, num_clients: int
) -> Tuple[np.ndarray, np.ndarray, int]:
    """Load SUMO dataset and partition by vehicle_id."""
    df = pd.read_csv(csv_path)
    
    # Get unique vehicle IDs and partition them
    vehicle_ids = sorted(df["vehicle_id"].unique())
    vehicles_per_client = len(vehicle_ids) / num_clients
    
    start_idx = int(client_id * vehicles_per_client)
    end_idx = int((client_id + 1) * vehicles_per_client)
    
    client_vehicles = vehicle_ids[start_idx:end_idx]
    
    # Filter data for this client's vehicles
    client_df = df[df["vehicle_id"].isin(client_vehicles)]
    
    # Extract features and labels
    feature_cols = ["gps_speed", "ble_rssi", "imu_magnitude"]
    X = client_df[feature_cols].values.astype(np.float32)
    y = (client_df["label"] == "parked").values.astype(np.float32)
    
    logger.info(
        f"Loaded {len(client_df)} samples for client {client_id} "
        f"({len(client_vehicles)} vehicles)"
    )
    logger.info(f"  Class distribution: {np.sum(y == 0):.0f} moving, {np.sum(y == 1):.0f} parked")
    
    return X, y, len(client_df)


# ============================================================================
# Local Training
# ============================================================================

def compute_class_weight(y: np.ndarray) -> float:
    """Compute pos_weight for BCEWithLogitsLoss."""
    n_positive = np.sum(y == 1)
    n_negative = np.sum(y == 0)
    if n_positive == 0:
        return 1.0
    return n_negative / n_positive


def train_local_model(
    model: nn.Module,
    X_train: np.ndarray,
    y_train: np.ndarray,
    epochs: int = LOCAL_EPOCHS,
) -> float:
    """Train model locally for N epochs. Return final loss."""
    # Create data loader
    X_tensor = torch.from_numpy(X_train)
    y_tensor = torch.from_numpy(y_train)
    dataset = TensorDataset(X_tensor, y_tensor)
    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)
    
    # Compute class weight
    pos_weight = compute_class_weight(y_train)
    
    # Setup training
    model.train()
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    loss_fn = nn.BCEWithLogitsLoss(pos_weight=torch.tensor(pos_weight, device=DEVICE))
    
    total_loss = 0.0
    
    for epoch in range(epochs):
        epoch_loss = 0.0
        for X_batch, y_batch in dataloader:
            X_batch, y_batch = X_batch.to(DEVICE), y_batch.to(DEVICE)
            
            # Forward pass
            logits = model(X_batch)
            loss = loss_fn(logits, y_batch.unsqueeze(1))
            
            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            epoch_loss += loss.item() * X_batch.size(0)
        
        epoch_loss /= len(dataset)
        total_loss = epoch_loss
    
    return total_loss


def evaluate_local_model(
    model: nn.Module,
    X_test: np.ndarray,
    y_test: np.ndarray,
) -> float:
    """Evaluate model accuracy on local test data."""
    X_tensor = torch.from_numpy(X_test).to(DEVICE)
    y_tensor = torch.from_numpy(y_test)
    
    model.eval()
    with torch.no_grad():
        logits = model(X_tensor)
        probs = torch.sigmoid(logits).squeeze().cpu().numpy()
        preds = (probs > 0.5).astype(int)
    
    accuracy = np.mean(preds == y_test)
    return accuracy



class FLClient:
    """Federated Learning Client."""
    
    def __init__(
        self,
        server_url: str,
        client_id: str,
        num_clients: int,
        rounds: int,
        local_epochs: int,
    ):
        """Initialize client."""
        self.server_url = server_url
        self.client_id = client_id
        self.num_clients = num_clients
        self.rounds = rounds
        self.local_epochs = local_epochs
        
        # Parse client index from ID
        self.client_idx = int(client_id.split("_")[-1])
        
        # Load data
        csv_path = backend_dir / "app" / "ml" / "data" / "sumo_dataset.csv"
        X, y, num_samples = load_and_partition_data(csv_path, self.client_idx, num_clients)
        
        # Split into train and test (80/20 local)
        split_idx = int(0.8 * len(X))
        self.X_train, self.X_test = X[:split_idx], X[split_idx:]
        self.y_train, self.y_test = y[:split_idx], y[split_idx:]
        self.num_samples = len(self.X_train)
        
        # Model
        self.model = ParkingStateClassifier().to(DEVICE)
        
        logger.info(f"Client {client_id} initialized with {self.num_samples} training samples")
    
    def register(self) -> bool:
        """Register with server."""
        try:
            response = requests.post(
                f"{self.server_url}/register_client",
                json={"client_id": self.client_id, "num_samples": self.num_samples},
                timeout=5,
            )
            response.raise_for_status()
            logger.info(f"Registered with server: {response.json()}")
            return True
        except Exception as e:
            logger.error(f"Registration failed: {e}")
            return False
    
    def download_global_model(self) -> bool:
        """Download global model from server."""
        try:
            response = requests.get(f"{self.server_url}/global_model", timeout=10)
            response.raise_for_status()
            weights = response.json()
            
            # Deserialize and load
            state_dict = {}
            for k, v in weights.items():
                state_dict[k] = torch.tensor(v, dtype=torch.float32)
            
            self.model.load_state_dict(state_dict)
            logger.info("Downloaded global model")
            return True
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return False
    
    def upload_weights(self, round_num: int) -> bool:
        """Upload trained weights to server."""
        try:
            # Serialize weights
            weights = {}
            for k, v in self.model.state_dict().items():
                weights[k] = v.detach().cpu().numpy().tolist()
            
            payload = {
                "client_id": self.client_id,
                "round_num": round_num,
                "weights": weights,
                "num_samples": self.num_samples,
            }
            
            logger.info(f"Uploading weights for round {round_num}:")
            logger.info(f"  client_id: {payload['client_id']}")
            logger.info(f"  round_num: {payload['round_num']}")
            logger.info(f"  num_samples: {payload['num_samples']}")
            logger.info(f"  weights keys: {list(payload['weights'].keys())}")
            logger.debug(f"  Full payload: {payload}")
            
            response = requests.post(
                f"{self.server_url}/submit_update",
                json=payload,
                timeout=10,
            )
            response.raise_for_status()
            logger.info(f"Uploaded weights for round {round_num}")
            return True
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"  Status: {e.response.status_code}")
                logger.error(f"  Response: {e.response.text}")
            return False
    
    def run(self) -> int:
        """Main client loop. Returns 0 on success, non-zero on failure."""
        logger.info(f"Starting client loop for {self.rounds} rounds...")
        
        failed_rounds = []
        
        for round_num in range(self.rounds):
            logger.info(f"\n=== Round {round_num} ===")
            
            # Download global model
            if not self.download_global_model():
                logger.error("Failed to download model, retrying once...")
                time.sleep(2)
                if not self.download_global_model():
                    logger.error(f"Failed to download model after retry. Aborting round {round_num}.")
                    failed_rounds.append((round_num, "model_download_failed"))
                    continue
            
            # Train locally
            logger.info(f"Training for {self.local_epochs} epochs...")
            loss = train_local_model(self.model, self.X_train, self.y_train, self.local_epochs)
            logger.info(f"Local training complete. Final loss: {loss:.4f}")
            
            # Evaluate locally
            acc = evaluate_local_model(self.model, self.X_test, self.y_test)
            logger.info(f"Local test accuracy: {acc:.4f}")
            
            # Upload weights - retry up to 3 times
            max_upload_attempts = 3
            for attempt in range(max_upload_attempts):
                if self.upload_weights(round_num):
                    logger.info(f"Round {round_num} complete. Waiting for next round...")
                    time.sleep(1)
                    break
                else:
                    logger.error(f"Failed to upload weights for round {round_num} (attempt {attempt + 1}/{max_upload_attempts})")
                    if attempt < max_upload_attempts - 1:
                        logger.info(f"Retrying upload in 2 seconds...")
                        time.sleep(2)
            else:
                # All upload attempts failed
                logger.error(f"CRITICAL: Failed to upload weights for round {round_num} after {max_upload_attempts} attempts. Aborting.")
                failed_rounds.append((round_num, "upload_failed"))
        
        # Summary and exit status
        if failed_rounds:
            logger.error(f"\n{'='*80}")
            logger.error(f"FAILED ROUNDS: {len(failed_rounds)}/{self.rounds}")
            for round_num, reason in failed_rounds:
                logger.error(f"  Round {round_num}: {reason}")
            logger.error(f"{'='*80}")
            logger.error("Client exiting with FAILURE status")
            return 1
        else:
            logger.info("\n" + "="*80)
            logger.info("Client finished all rounds successfully!")
            logger.info("="*80)
            return 0


# ============================================================================
# Main
# ============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Federated Learning Client")
    parser.add_argument("--server_url", type=str, default="http://localhost:8000")
    parser.add_argument("--client_id", type=str, required=True)
    parser.add_argument("--num_clients", type=int, default=5)
    parser.add_argument("--rounds", type=int, default=10)
    parser.add_argument("--local_epochs", type=int, default=3)
    
    args = parser.parse_args()
    
    client = FLClient(
        server_url=args.server_url,
        client_id=args.client_id,
        num_clients=args.num_clients,
        rounds=args.rounds,
        local_epochs=args.local_epochs,
    )
    
    # Register and run
    if client.register():
        exit_code = client.run()
        sys.exit(exit_code)
    else:
        logger.error("Failed to register. Exiting.")
        sys.exit(1)


if __name__ == "__main__":
    main()
