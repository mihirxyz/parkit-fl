#!/usr/bin/env python3
"""
FL Experiment Orchestrator

Starts FL server and 5 clients as separate processes.
Runs 10 rounds of federated learning.
Logs global model accuracy after each round.
Outputs results to backend/app/ml/results/fl_metrics.json
"""

import json
import logging
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd
import requests
import torch

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("fl_orchestrator")

# Paths
BACKEND_DIR = Path(__file__).resolve().parent / "backend"
FL_SERVER_SCRIPT = BACKEND_DIR / "app" / "ml" / "fl_server.py"
FL_CLIENT_SCRIPT = Path(__file__).resolve().parent / "fl_clients" / "client.py"
DATA_PATH = BACKEND_DIR / "app" / "ml" / "data" / "sumo_dataset.csv"
RESULTS_DIR = BACKEND_DIR / "app" / "ml" / "results"
RESULTS_FILE = RESULTS_DIR / "fl_metrics.json"
LOGS_DIR = Path(__file__).resolve().parent / "fl_clients" / "logs"

# Configuration
SERVER_URL = "http://localhost:8000"
NUM_CLIENTS = 5
NUM_ROUNDS = 10
LOCAL_EPOCHS = 3


# ============================================================================
# Logging Setup
# ============================================================================

def setup_client_logging(client_id: int) -> Path:
    """Create log file path for a client."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / f"client_{client_id}.log"
    return log_file


# ============================================================================
# Server Management
# ============================================================================

def start_server() -> Optional[subprocess.Popen]:
    """Start FL server in subprocess."""
    logger.info("Starting FL server...")
    try:
        venv_python = BACKEND_DIR / ".venv" / "Scripts" / "python.exe"
        server_log_file = LOGS_DIR / "fl_server_process.log"
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        
        log_f = open(server_log_file, "a")
        process = subprocess.Popen(
            [str(venv_python), str(FL_SERVER_SCRIPT)],
            cwd=str(BACKEND_DIR),
            stdout=log_f,
            stderr=subprocess.STDOUT,
            text=True,
        )
        
        logger.info(f"Server process started (PID: {process.pid}), logging to {server_log_file}")
        return process
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        return None


def wait_for_server(max_retries: int = 30, retry_interval: int = 1) -> bool:
    """Poll server until it's ready."""
    logger.info("Waiting for server to be ready...")
    
    for attempt in range(max_retries):
        try:
            response = requests.get(f"{SERVER_URL}/health", timeout=2)
            if response.status_code == 200:
                logger.info("Server is ready!")
                return True
        except requests.exceptions.ConnectionError:
            logger.debug(f"Server not ready yet (attempt {attempt + 1}/{max_retries})")
            time.sleep(retry_interval)
    
    logger.error("Server did not become ready in time")
    return False


def check_server_health() -> bool:
    """Check if server is still responsive."""
    try:
        response = requests.get(f"{SERVER_URL}/health", timeout=2)
        return response.status_code == 200
    except Exception:
        return False


# ============================================================================
# Client Management
# ============================================================================

def start_clients() -> List[subprocess.Popen]:
    """Start 5 FL client processes with logging."""
    logger.info(f"Starting {NUM_CLIENTS} clients...")
    
    venv_python = BACKEND_DIR / ".venv" / "Scripts" / "python.exe"
    client_processes = []
    
    for client_idx in range(NUM_CLIENTS):
        client_id = f"client_{client_idx}"
        log_file = setup_client_logging(client_idx)
        
        try:
            with open(log_file, "w") as f:
                f.write(f"Client {client_id} started at {datetime.now().isoformat()}\n")
                f.write("=" * 80 + "\n\n")
            
            process = subprocess.Popen(
                [
                    str(venv_python),
                    str(FL_CLIENT_SCRIPT),
                    "--server_url", SERVER_URL,
                    "--client_id", client_id,
                    "--num_clients", str(NUM_CLIENTS),
                    "--rounds", str(NUM_ROUNDS),
                    "--local_epochs", str(LOCAL_EPOCHS),
                ],
                stdout=open(log_file, "a"),
                stderr=subprocess.STDOUT,
                text=True,
            )
            
            client_processes.append(process)
            logger.info(f"Started client {client_id} (PID: {process.pid}), logging to {log_file}")
            time.sleep(0.5)
        
        except Exception as e:
            logger.error(f"Failed to start client {client_id}: {e}")
    
    return client_processes


def check_client_alive(process: subprocess.Popen, client_idx: int) -> bool:
    """Check if a client process is still alive or completed normally."""
    poll_result = process.poll()
    if poll_result is not None:
        if poll_result == 0:
            # Completed all rounds successfully
            return True
        # Process is dead with non-zero exit code
        logger.error(f"Client {client_idx} died with exit code {poll_result}")
        # Read logs and print them
        log_file = LOGS_DIR / f"client_{client_idx}.log"
        if log_file.exists():
            logger.error(f"Last 50 lines of client {client_idx} logs:")
            try:
                with open(log_file, "r") as f:
                    lines = f.readlines()[-50:]
                    for line in lines:
                        logger.error(f"  {line.rstrip()}")
            except Exception as e:
                logger.error(f"Could not read log file: {e}")
        return False
    return True


# ============================================================================
# Evaluation
# ============================================================================

def load_test_data() -> tuple:
    """Load held-out test data for evaluation."""
    df = pd.read_csv(DATA_PATH)
    
    # Use deterministic split (last 15% as test)
    test_split = int(0.85 * len(df))
    test_df = df.iloc[test_split:]
    
    feature_cols = ["gps_speed", "ble_rssi", "imu_magnitude"]
    X_test = test_df[feature_cols].values.astype(np.float32)
    y_test = (test_df["label"] == "parked").values.astype(np.float32)
    
    logger.info(f"Loaded {len(test_df)} test samples")
    return X_test, y_test


def evaluate_global_model(round_num: int, X_test: np.ndarray, y_test: np.ndarray) -> dict:
    """Download global model and evaluate on test set."""
    try:
        from sklearn.metrics import accuracy_score, precision_recall_fscore_support
        
        # Get global model weights
        response = requests.get(f"{SERVER_URL}/global_model", timeout=10)
        response.raise_for_status()
        weights = response.json()
        
        # Load model
        sys.path.insert(0, str(BACKEND_DIR))
        from app.ml.model import ParkingStateClassifier
        
        model = ParkingStateClassifier()
        state_dict = {}
        for k, v in weights.items():
            state_dict[k] = torch.tensor(v, dtype=torch.float32)
        model.load_state_dict(state_dict)
        
        # Evaluate
        X_tensor = torch.from_numpy(X_test)
        model.eval()
        with torch.no_grad():
            logits = model(X_tensor)
            probs = torch.sigmoid(logits).squeeze().numpy()
            preds = (probs > 0.5).astype(int)
        
        accuracy = accuracy_score(y_test, preds)
        precision_macro, recall_macro, f1_macro, _ = precision_recall_fscore_support(
            y_test, preds, average="macro"
        )
        precision_per_class, recall_per_class, f1_per_class, _ = precision_recall_fscore_support(
            y_test, preds, average=None
        )
        
        metrics = {
            "round": round_num,
            "accuracy": float(accuracy),
            "precision_macro": float(precision_macro),
            "recall_macro": float(recall_macro),
            "f1_macro": float(f1_macro),
            "precision_moving": float(precision_per_class[0]),
            "recall_moving": float(recall_per_class[0]),
            "f1_moving": float(f1_per_class[0]),
            "precision_parked": float(precision_per_class[1]),
            "recall_parked": float(recall_per_class[1]),
            "f1_parked": float(f1_per_class[1]),
        }
        
        logger.info(f"Round {round_num}: accuracy={accuracy:.4f}, f1_macro={f1_macro:.4f}")
        return metrics
    
    except Exception as e:
        logger.error(f"Evaluation failed for round {round_num}: {e}")
        return None


def wait_for_round_completion(
    round_num: int, 
    client_processes: List[subprocess.Popen],
    timeout: int = 600
) -> bool:
    """Poll server until round is complete, with health checks."""
    start_time = time.time()
    last_status = 0
    
    while time.time() - start_time < timeout:
        elapsed = time.time() - start_time
        
        # Check round status first
        try:
            response = requests.get(
                f"{SERVER_URL}/round_status",
                params={"round_num": round_num},
                timeout=5,
            )
            response.raise_for_status()
            status = response.json()
            
            # Log progress every 30 seconds
            if elapsed > last_status + 30:
                logger.info(
                    f"Round {round_num}: {status['clients_participated']}/{status['clients_total']} "
                    f"clients ready (elapsed: {int(elapsed)}s)"
                )
                last_status = elapsed
            
            if status["round_complete"] or status["current_round"] > round_num:
                logger.info(f"Round {round_num} complete: {status['clients_participated']}/{status['clients_total']} clients")
                return True
        except Exception as e:
            logger.debug(f"Status check failed: {e}")
        
        # Check server health
        if not check_server_health():
            logger.error(f"Server became unresponsive during round {round_num} (elapsed: {elapsed:.1f}s)")
            return False
        
        # Check all client processes
        for idx, process in enumerate(client_processes):
            if not check_client_alive(process, idx):
                logger.error(f"Client {idx} died during round {round_num} (elapsed: {elapsed:.1f}s)")
                return False
        
        time.sleep(1)
    
    logger.error(f"Round {round_num} did not complete in {timeout}s (timeout)")
    return False
    


# ============================================================================
# Orchestration
# ============================================================================

def run_experiment() -> None:
    """Run full FL experiment."""
    logger.info("=" * 80)
    logger.info("FEDERATED LEARNING EXPERIMENT")
    logger.info("=" * 80)
    
    start_time = datetime.now()
    logger.info(f"Experiment started at {start_time}")
    
    # Ensure results directory exists
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Start server
    server_process = start_server()
    if not server_process:
        logger.error("Failed to start server")
        return
    
    time.sleep(2)
    
    # Wait for server to be ready
    if not wait_for_server():
        logger.error("Server failed to become ready")
        server_process.terminate()
        return
    
    # Load test data
    X_test, y_test = load_test_data()
    
    # Start clients
    client_processes = start_clients()
    if not client_processes:
        logger.error("Failed to start clients")
        server_process.terminate()
        return
    
    # Run experiment rounds
    logger.info(f"Running {NUM_ROUNDS} federated rounds...")
    
    round_metrics = []
    
    for round_num in range(NUM_ROUNDS):
        logger.info(f"\n--- Waiting for round {round_num} to complete ---")
        
        # Wait for round completion with health checks
        if wait_for_round_completion(round_num, client_processes, timeout=600):
            # Evaluate global model
            time.sleep(0.5)
            metrics = evaluate_global_model(round_num, X_test, y_test)
            
            if metrics:
                round_metrics.append(metrics)
        else:
            logger.error(f"Round {round_num} timed out")
    
    # Wait for all clients to finish
    logger.info("\nWaiting for clients to finish...")
    for i, process in enumerate(client_processes):
        try:
            process.wait(timeout=60)
            logger.info(f"Client {i} finished")
        except subprocess.TimeoutExpired:
            logger.warning(f"Client {i} timed out, terminating")
            process.terminate()
    
    # Shutdown server
    logger.info("Shutting down server...")
    server_process.terminate()
    try:
        server_process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        server_process.kill()
    
    # Save results
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    results = {
        "experiment": {
            "type": "federated_learning",
            "num_clients": NUM_CLIENTS,
            "num_rounds": NUM_ROUNDS,
            "local_epochs": LOCAL_EPOCHS,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
        },
        "global_model_history": round_metrics,
    }
    
    # Add summary statistics
    if round_metrics:
        accuracies = [m["accuracy"] for m in round_metrics]
        results["summary"] = {
            "final_accuracy": accuracies[-1],
            "best_accuracy": max(accuracies),
            "mean_accuracy": float(np.mean(accuracies)),
            "std_accuracy": float(np.std(accuracies)),
        }
    
    # Write results
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"\nResults saved to {RESULTS_FILE}")
    logger.info("=" * 80)
    logger.info("EXPERIMENT COMPLETE")
    logger.info("=" * 80)
    
    # Print summary
    if round_metrics:
        accuracies = [m["accuracy"] for m in round_metrics]
        print("\nFederated Learning Results Summary:")
        print(f"  Final accuracy: {accuracies[-1]:.4f}")
        print(f"  Best accuracy: {max(accuracies):.4f}")
        print(f"  Mean accuracy: {np.mean(accuracies):.4f}")
        print(f"  Total time: {duration:.1f} seconds")


if __name__ == "__main__":
    run_experiment()
