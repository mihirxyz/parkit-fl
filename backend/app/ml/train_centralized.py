#!/usr/bin/env python3
"""
Centralized training baseline for parking state classifier.

Trains a PyTorch MLP on sensor data with stratified train/val/test split.
Handles class imbalance (73% parked, 27% moving) with weighted loss.
Reports class-wise precision/recall/F1 for both parked and moving states.
"""

import json
import sys
from pathlib import Path
from typing import Any, Tuple

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, TensorDataset

# Add backend to path so we can import app modules
_backend_dir = Path(__file__).resolve().parents[2]
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from app.ml.model import ParkingStateClassifier


DATA_PATH = Path(__file__).resolve().parent / "data" / "sumo_dataset.csv"
RESULTS_DIR = Path(__file__).resolve().parent / "results"
MODEL_WEIGHTS_PATH = Path(__file__).resolve().parent / "model_weights.pth"
METRICS_PATH = RESULTS_DIR / "centralized_metrics.json"

# Training hyperparameters
BATCH_SIZE = 32
LEARNING_RATE = 0.001
EPOCHS = 30
EARLY_STOPPING_PATIENCE = 5
TRAIN_VAL_TEST_SPLIT = (0.7, 0.15, 0.15)
RANDOM_SEED = 42

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def load_dataset(csv_path: Path) -> Tuple[np.ndarray, np.ndarray]:
    """Load SUMO dataset and extract features/labels."""
    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset not found: {csv_path}")
    
    df = pd.read_csv(csv_path)
    
    # Extract features: gps_speed, ble_rssi, imu_magnitude
    feature_cols = ["gps_speed", "ble_rssi", "imu_magnitude"]
    X = df[feature_cols].values.astype(np.float32)
    
    # Encode labels: parked=1, moving=0
    y = (df["label"] == "parked").values.astype(np.float32)
    
    return X, y


def split_stratified(
    X: np.ndarray, y: np.ndarray, train_ratio: float = 0.7, val_ratio: float = 0.15
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Stratified train/val/test split to preserve class ratios.
    
    Args:
        X: Feature matrix (n_samples, n_features)
        y: Label vector (n_samples,)
        train_ratio: Fraction for training (default 0.7)
        val_ratio: Fraction for validation (default 0.15, test gets remainder)
    
    Returns:
        X_train, X_val, X_test, y_train, y_val, y_test
    """
    # First split: train vs (val+test)
    test_ratio = 1.0 - train_ratio - val_ratio
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=(val_ratio + test_ratio), stratify=y, random_state=RANDOM_SEED
    )
    
    # Second split: val vs test (stratify on remaining data)
    val_test_ratio = val_ratio / (val_ratio + test_ratio)
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=(1.0 - val_test_ratio), stratify=y_temp, random_state=RANDOM_SEED
    )
    
    return X_train, X_val, X_test, y_train, y_val, y_test




def train_epoch(
    model: nn.Module,
    train_loader: DataLoader,
    loss_fn: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
) -> float:
    """Train for one epoch and return average loss."""
    model.train()
    total_loss = 0.0
    
    for X_batch, y_batch in train_loader:
        X_batch, y_batch = X_batch.to(device), y_batch.to(device)
        
        # Forward pass
        logits = model(X_batch)
        loss = loss_fn(logits, y_batch.unsqueeze(1))
        
        # Backward pass
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item() * X_batch.size(0)
    
    return total_loss / len(train_loader.dataset)


def evaluate(
    model: nn.Module,
    val_loader: DataLoader,
    loss_fn: nn.Module,
    device: torch.device,
) -> Tuple[float, np.ndarray, np.ndarray]:
    """Evaluate on validation/test set and return loss, predictions, true labels."""
    model.eval()
    total_loss = 0.0
    all_preds = []
    all_targets = []
    
    with torch.no_grad():
        for X_batch, y_batch in val_loader:
            X_batch, y_batch = X_batch.to(device), y_batch.to(device)
            
            logits = model(X_batch)
            loss = loss_fn(logits, y_batch.unsqueeze(1))
            total_loss += loss.item() * X_batch.size(0)
            
            # Get binary predictions (threshold 0.5 on probabilities)
            probs = torch.sigmoid(logits).squeeze()
            preds = (probs > 0.5).cpu().numpy().astype(int)
            all_preds.extend(preds)
            all_targets.extend(y_batch.cpu().numpy().astype(int))
    
    avg_loss = total_loss / len(val_loader.dataset)
    return avg_loss, np.array(all_preds), np.array(all_targets)


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """
    Compute comprehensive metrics including class-wise precision/recall/F1.
    
    Returns dict with:
    - overall: accuracy, macro F1, weighted F1
    - per_class: metrics for each class (parked and moving)
    - confusion_matrix: TP, FP, TN, FN
    """
    # Overall metrics
    accuracy = accuracy_score(y_true, y_pred)
    precision_macro, recall_macro, f1_macro, _ = precision_recall_fscore_support(
        y_true, y_pred, average="macro"
    )
    precision_weighted, recall_weighted, f1_weighted, _ = precision_recall_fscore_support(
        y_true, y_pred, average="weighted"
    )
    
    # Per-class metrics
    precision_per_class, recall_per_class, f1_per_class, support = precision_recall_fscore_support(
        y_true, y_pred, average=None
    )
    
    # Confusion matrix
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    
    return {
        "overall": {
            "accuracy": float(accuracy),
            "precision_macro": float(precision_macro),
            "recall_macro": float(recall_macro),
            "f1_macro": float(f1_macro),
            "precision_weighted": float(precision_weighted),
            "recall_weighted": float(recall_weighted),
            "f1_weighted": float(f1_weighted),
        },
        "per_class": {
            "moving": {
                "precision": float(precision_per_class[0]),
                "recall": float(recall_per_class[0]),
                "f1": float(f1_per_class[0]),
                "support": int(support[0]),
            },
            "parked": {
                "precision": float(precision_per_class[1]),
                "recall": float(recall_per_class[1]),
                "f1": float(f1_per_class[1]),
                "support": int(support[1]),
            },
        },
        "confusion_matrix": {
            "true_negatives": int(tn),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "true_positives": int(tp),
        },
    }


def compute_class_weights(y: np.ndarray) -> float:
    """Compute pos_weight for BCEWithLogitsLoss."""
    n_positive = np.sum(y == 1)
    n_negative = np.sum(y == 0)
    pos_weight = n_negative / n_positive
    return pos_weight


def train_model(
    X_train: np.ndarray,
    X_val: np.ndarray,
    X_test: np.ndarray,
    y_train: np.ndarray,
    y_val: np.ndarray,
    y_test: np.ndarray,
) -> Tuple[nn.Module, dict, dict]:
    """Train the model with early stopping and evaluate on test set."""
    # Convert to tensors
    X_train_t = torch.from_numpy(X_train)
    y_train_t = torch.from_numpy(y_train)
    X_val_t = torch.from_numpy(X_val)
    y_val_t = torch.from_numpy(y_val)
    X_test_t = torch.from_numpy(X_test)
    y_test_t = torch.from_numpy(y_test)
    
    # Create data loaders
    train_dataset = TensorDataset(X_train_t, y_train_t)
    val_dataset = TensorDataset(X_val_t, y_val_t)
    test_dataset = TensorDataset(X_test_t, y_test_t)
    
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False)
    
    # Initialize model
    model = ParkingStateClassifier(input_size=3, hidden1=16, hidden2=8).to(DEVICE)
    
    # Compute class weights for imbalanced data
    pos_weight = compute_class_weights(y_train)
    print(f"\nClass weights:")
    print(f"  Positive class (parked) weight: {pos_weight:.4f}")
    print(f"  Class distribution: {np.sum(y_train == 0):.0f} moving, {np.sum(y_train == 1):.0f} parked")
    
    # Loss and optimizer
    loss_fn = nn.BCEWithLogitsLoss(pos_weight=torch.tensor(pos_weight, device=DEVICE))
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    
    # Training loop with early stopping
    train_history = []
    best_val_loss = float("inf")
    patience_counter = 0
    best_model_state = None
    
    print(f"\nTraining for up to {EPOCHS} epochs (early stopping patience={EARLY_STOPPING_PATIENCE})...")
    
    for epoch in range(EPOCHS):
        train_loss = train_epoch(model, train_loader, loss_fn, optimizer, DEVICE)
        val_loss, _, _ = evaluate(model, val_loader, loss_fn, DEVICE)
        
        train_history.append({"epoch": epoch + 1, "train_loss": train_loss, "val_loss": val_loss})
        
        if (epoch + 1) % 5 == 0 or epoch == 0:
            print(f"  Epoch {epoch + 1:2d}/{EPOCHS} | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f}")
        
        # Early stopping
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            best_model_state = model.state_dict().copy()
        else:
            patience_counter += 1
            if patience_counter >= EARLY_STOPPING_PATIENCE:
                print(f"  Early stopping triggered at epoch {epoch + 1}")
                break
    
    # Restore best model
    if best_model_state is not None:
        model.load_state_dict(best_model_state)
    
    # Evaluate on test set
    print(f"\nEvaluating on test set...")
    test_loss, test_preds, test_targets = evaluate(model, test_loader, loss_fn, DEVICE)
    test_metrics = compute_metrics(test_targets, test_preds)
    
    return model, train_history, test_metrics


def print_metrics(metrics: dict) -> None:
    """Pretty-print evaluation metrics with per-class breakdown."""
    print("\n" + "=" * 70)
    print("TEST SET EVALUATION RESULTS")
    print("=" * 70)
    
    # Overall metrics
    print("\nOVERALL METRICS:")
    print(f"  Accuracy:           {metrics['overall']['accuracy']:.4f}")
    print(f"  Precision (macro):  {metrics['overall']['precision_macro']:.4f}")
    print(f"  Recall (macro):     {metrics['overall']['recall_macro']:.4f}")
    print(f"  F1-score (macro):   {metrics['overall']['f1_macro']:.4f}")
    print(f"  Precision (weighted): {metrics['overall']['precision_weighted']:.4f}")
    print(f"  Recall (weighted):  {metrics['overall']['recall_weighted']:.4f}")
    print(f"  F1-score (weighted): {metrics['overall']['f1_weighted']:.4f}")
    
    # Per-class metrics
    print("\nPER-CLASS METRICS:")
    print(f"\n  MOVING (class 0, minority):")
    print(f"    Precision: {metrics['per_class']['moving']['precision']:.4f}")
    print(f"    Recall:    {metrics['per_class']['moving']['recall']:.4f}")
    print(f"    F1-score:  {metrics['per_class']['moving']['f1']:.4f}")
    print(f"    Support:   {metrics['per_class']['moving']['support']} samples")
    
    print(f"\n  PARKED (class 1, majority):")
    print(f"    Precision: {metrics['per_class']['parked']['precision']:.4f}")
    print(f"    Recall:    {metrics['per_class']['parked']['recall']:.4f}")
    print(f"    F1-score:  {metrics['per_class']['parked']['f1']:.4f}")
    print(f"    Support:   {metrics['per_class']['parked']['support']} samples")
    
    # Confusion matrix
    cm = metrics['confusion_matrix']
    print(f"\nCONFUSION MATRIX:")
    print(f"                 Predicted Moving  Predicted Parked")
    print(f"  Actual Moving:  {cm['true_negatives']:6d}            {cm['false_positives']:6d}")
    print(f"  Actual Parked:  {cm['false_negatives']:6d}            {cm['true_positives']:6d}")
    


def main() -> int:
    """Main training pipeline."""
    print("=" * 70)
    print("CENTRALIZED BASELINE TRAINING")
    print("=" * 70)
    
    # Load dataset
    print(f"\nLoading dataset from {DATA_PATH}...")
    X, y = load_dataset(DATA_PATH)
    print(f"  Loaded {X.shape[0]} samples with {X.shape[1]} features")
    print(f"  Class distribution: {np.sum(y == 0):.0f} moving ({100*np.sum(y == 0)/len(y):.1f}%), "
          f"{np.sum(y == 1):.0f} parked ({100*np.sum(y == 1)/len(y):.1f}%)")
    
    # Stratified split
    print(f"\nSplitting data (train/val/test = 70/15/15, stratified)...")
    X_train, X_val, X_test, y_train, y_val, y_test = split_stratified(X, y)
    print(f"  Train: {X_train.shape[0]} samples "
          f"({np.sum(y_train == 0):.0f} moving, {np.sum(y_train == 1):.0f} parked)")
    print(f"  Val:   {X_val.shape[0]} samples "
          f"({np.sum(y_val == 0):.0f} moving, {np.sum(y_val == 1):.0f} parked)")
    print(f"  Test:  {X_test.shape[0]} samples "
          f"({np.sum(y_test == 0):.0f} moving, {np.sum(y_test == 1):.0f} parked)")
    
    # Train model
    model, train_history, test_metrics = train_model(X_train, X_val, X_test, y_train, y_val, y_test)
    
    # Print results
    print_metrics(test_metrics)
    
    # Save model weights
    print(f"\nSaving model weights to {MODEL_WEIGHTS_PATH}...")
    MODEL_WEIGHTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), MODEL_WEIGHTS_PATH)
    print(f"  ✓ Model saved")
    
    # Save metrics
    print(f"Saving metrics to {METRICS_PATH}...")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    metrics_to_save = {
        "dataset": {
            "total_samples": int(X.shape[0]),
            "n_features": int(X.shape[1]),
            "class_distribution": {
                "moving": int(np.sum(y == 0)),
                "parked": int(np.sum(y == 1)),
            },
        },
        "training": {
            "train_samples": int(X_train.shape[0]),
            "val_samples": int(X_val.shape[0]),
            "test_samples": int(X_test.shape[0]),
            "epochs_run": len(train_history),
            "batch_size": BATCH_SIZE,
            "learning_rate": LEARNING_RATE,
        },
        "test_results": test_metrics,
    }
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics_to_save, f, indent=2)
    print(f"  ✓ Metrics saved")
    
    print("\n✓ Training complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())

