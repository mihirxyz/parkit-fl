#!/usr/bin/env python3
"""
Standalone training runner - executes the centralized training directly.
Run from the backend directory or anywhere with: python train_runner.py
"""
import subprocess
import sys
from pathlib import Path

def main():
    backend_root = Path(__file__).resolve().parent
    
    # Change to backend directory
    import os
    os.chdir(backend_root)
    
    # Run the training script
    script = backend_root / "app" / "ml" / "train_centralized.py"
    venv_python = backend_root / ".venv" / "Scripts" / "python.exe"
    
    print(f"Backend root: {backend_root}")
    print(f"Python executable: {venv_python}")
    print(f"Training script: {script}")
    print(f"Data file exists: {(backend_root / 'app' / 'ml' / 'data' / 'sumo_dataset.csv').exists()}")
    print("\nStarting training...\n")
    print("=" * 80)
    
    # Run directly with subprocess (no shell, no environment variable issues)
    result = subprocess.run(
        [str(venv_python), str(script)],
        cwd=str(backend_root),
        capture_output=False,  # Show output in real-time
        text=True
    )
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
