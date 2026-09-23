#!/usr/bin/env python3
"""Direct runner for training without subprocess."""
import sys
import os

# Set up path
sys.path.insert(0, r"C:\Users\inamd\Desktop\parkit-fl\backend")
os.chdir(r"C:\Users\inamd\Desktop\parkit-fl\backend")

# Import and run
from app.ml.train_centralized import main

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
