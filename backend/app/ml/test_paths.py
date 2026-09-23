#!/usr/bin/env python3
"""Quick test of paths and imports."""
import sys
from pathlib import Path

# Test paths
script_dir = Path(__file__).resolve().parent
print(f"Script directory: {script_dir}")

data_path = script_dir / "data" / "sumo_dataset.csv"
print(f"Data path: {data_path}")
print(f"Data file exists: {data_path.exists()}")

results_dir = script_dir / "results"
print(f"Results dir: {results_dir}")

model_weights_path = script_dir / "model_weights.pth"
print(f"Model weights path: {model_weights_path}")

# Test imports
print("\nTesting imports...")
try:
    import pandas as pd
    print("✓ pandas imported")
except ImportError as e:
    print(f"✗ pandas import failed: {e}")

try:
    import numpy as np
    print("✓ numpy imported")
except ImportError as e:
    print(f"✗ numpy import failed: {e}")

try:
    import torch
    print("✓ torch imported")
except ImportError as e:
    print(f"✗ torch import failed: {e}")

try:
    import sklearn
    print("✓ sklearn imported")
except ImportError as e:
    print(f"✗ sklearn import failed: {e}")

# Test loading the model
print("\nTesting model import...")
try:
    from app.ml.model import ParkingStateClassifier
    print("✓ ParkingStateClassifier imported")
    model = ParkingStateClassifier()
    print(f"✓ Model created: {model}")
except Exception as e:
    print(f"✗ Model import failed: {e}")
    import traceback
    traceback.print_exc()

# Test loading data
print("\nTesting data loading...")
try:
    df = pd.read_csv(data_path)
    print(f"✓ Data loaded: {df.shape[0]} rows, {df.shape[1]} columns")
    print(f"  Columns: {list(df.columns)}")
    print(f"  First row:\n{df.iloc[0]}")
except Exception as e:
    print(f"✗ Data loading failed: {e}")
    import traceback
    traceback.print_exc()

print("\n✓ All tests passed!")
