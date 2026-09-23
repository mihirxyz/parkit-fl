"""
Database initialisation and migration script.

Usage:
    # From the backend directory (with venv activated):
    python -m app.db.init_db

    # Or directly:
    python backend/app/db/init_db.py

Creates all tables and seeds the Pune NxN parking-zone grid if the
parking_zones table is empty. Safe to re-run (idempotent).
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running as a standalone script from any working directory.
_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.grid.grid_service import PUNE_BOUNDS, init_grid_zones  # noqa: E402

# Register all ORM models so metadata is fully populated before create_all.
import app.db.models  # noqa: F401,E402


def create_tables() -> None:
    """Create all SQLAlchemy-managed tables (no-op if already present)."""
    Base.metadata.create_all(bind=engine)
    print("[init_db] All tables created / verified.")


def seed_zones(n: int = 3) -> None:
    """Seed the parking_zones table with the NxN Pune grid if empty."""
    with SessionLocal() as db:
        zones = init_grid_zones(db, n=n)
    print(
        f"[init_db] Grid seeded: {len(zones)} zone(s), "
        f"{n}×{n} grid over Pune bounds "
        f"lat [{PUNE_BOUNDS['lat_min']}, {PUNE_BOUNDS['lat_max']}] "
        f"lon [{PUNE_BOUNDS['lon_min']}, {PUNE_BOUNDS['lon_max']}]."
    )


def init_db(n: int = 3) -> None:
    """Full initialisation: create tables then seed zones."""
    create_tables()
    seed_zones(n=n)
    print("[init_db] Initialisation complete.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Initialise the Parkit SQLite database.")
    parser.add_argument(
        "--n",
        type=int,
        default=3,
        help="Grid resolution: NxN parking zones (default: 3 → 9 zones).",
    )
    args = parser.parse_args()
    init_db(n=args.n)
