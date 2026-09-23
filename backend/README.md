# Backend

The backend exposes versioned FastAPI endpoints and keeps concerns isolated by package:

- `api/`: request and response boundaries.
- `core/`: configuration and shared constants.
- `db/`: SQLAlchemy engine, session, and ORM entities.
- `grid/`: stable spatial-cell identifiers and coordinate mapping.
- `ml/`: local training contracts and federated aggregation.
- `simulation/`: adapters for external mobility simulators.

## Development

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest
uvicorn app.main:app --reload
```

By default the service uses a local SQLite database at `backend/parkit.db`. Override settings through `PARKIT_`-prefixed environment variables, for example `PARKIT_DATABASE_URL`.

## SUMO trajectory dataset

The versioned scenario files are in `app/simulation/sumo/`. The scenario contains 200 vehicle trips distributed across a 3,600-second run, plus designated-lot and roadside parking areas. Parking events use SUMO parking-area stops, so the `parked` label is based on the traffic simulator rather than arbitrary random assignment.

Install the Eclipse SUMO application and make `sumo` available on `PATH`, or set `SUMO_HOME` to its installation directory. Install Python dependencies, then generate the dataset from this directory:

```powershell
python -m app.simulation.run_simulation
```

This creates `app/ml/data/sumo_dataset.csv` with the columns `vehicle_id`, `timestep`, `lat`, `lon`, `gps_speed`, `ble_rssi`, `imu_magnitude`, and `label`. The CSV is intentionally Git-ignored because it is generated. The scenario configuration and default seed make generation reproducible.
