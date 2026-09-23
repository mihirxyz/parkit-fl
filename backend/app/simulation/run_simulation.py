from __future__ import annotations

import argparse
import csv
import math
import os
import random
import shutil
import sys
from pathlib import Path
from typing import Any

# Ensure the backend directory is on the Python path before importing app modules
# run_simulation.py is at backend/app/simulation/run_simulation.py
# parents[0]=simulation, parents[1]=app, parents[2]=backend
_backend_dir = Path(__file__).resolve().parents[2]
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from app.simulation.sensors import (
    derive_ble_rssi,
    derive_gps_speed,
    derive_imu_magnitude,
    nearest_beacon_distance,
)

SCENARIO_DIRECTORY = Path(__file__).resolve().parent / "sumo"
DEFAULT_CONFIG_PATH = SCENARIO_DIRECTORY / "parkit_grid.sumocfg"
DEFAULT_OUTPUT_PATH = Path(__file__).resolve().parents[1] / "ml" / "data" / "sumo_dataset.csv"
DATASET_COLUMNS = [
    "vehicle_id",
    "timestep",
    "lat",
    "lon",
    "gps_speed",
    "ble_rssi",
    "imu_magnitude",
    "label",
]
# Coordinates are in SUMO network metres and model fixed Bluetooth beacons near parking facilities.
BEACON_POSITIONS_METERS = ((140.0, 190.0), (195.0, 145.0), (340.0, 210.0), (205.0, 335.0))

# Pune city centre reference point (WGS84)
PUNE_CENTER_LAT = 18.5204
PUNE_CENTER_LON = 73.8567

# Network spans roughly 400m x 400m in SUMO coords (0-400).
# At Pune's latitude, 1 degree ≈ 111 km, so 400m ≈ 0.0036 degrees
# This matches the 0.004 degree span in parkit_grid.nod.xml
METERS_PER_DEGREE_LAT = 111000.0  # Constant across Earth
METERS_PER_DEGREE_LON = 111000.0 * math.cos(math.radians(PUNE_CENTER_LAT))


def sumo_coords_to_wgs84(x_sumo: float, y_sumo: float) -> tuple[float, float]:
    """
    Convert SUMO network coordinates (0-400 metres) to WGS84 lat/lon.
    
    The network spans 0-400m in both dimensions. This is mapped to approximately
    0.004° latitude and 0.0037° longitude around Pune centre (18.5204°N, 73.8567°E).
    """
    # Network spans 0-400m; map proportionally to geographic span
    # At Pune's latitude: 1° lat ≈ 111 km, 1° lon ≈ 93 km
    # So 400m ≈ 0.0036° lat, ≈ 0.0043° lon
    
    lat_span_degrees = 400.0 / METERS_PER_DEGREE_LAT  # ~0.0036°
    lon_span_degrees = 400.0 / METERS_PER_DEGREE_LON  # ~0.0043°
    
    # Normalize SUMO coordinates to 0-1 range
    x_norm = x_sumo / 400.0
    y_norm = y_sumo / 400.0
    
    # Map to geographic bounds centered on Pune
    lat_min = PUNE_CENTER_LAT - (lat_span_degrees / 2.0)
    lat_max = PUNE_CENTER_LAT + (lat_span_degrees / 2.0)
    lon_min = PUNE_CENTER_LON - (lon_span_degrees / 2.0)
    lon_max = PUNE_CENTER_LON + (lon_span_degrees / 2.0)
    
    lat = lat_min + (y_norm * lat_span_degrees)
    lon = lon_min + (x_norm * lon_span_degrees)
    
    return lat, lon



def find_sumo_binary(gui: bool = False) -> str:
    """Locate a SUMO executable from SUMO_HOME or the process PATH."""
    executable = "sumo-gui" if gui else "sumo"
    suffix = ".exe" if os.name == "nt" else ""
    sumo_home = os.environ.get("SUMO_HOME")
    if sumo_home:
        candidate = Path(sumo_home) / "bin" / f"{executable}{suffix}"
        if candidate.is_file():
            return str(candidate)

    path_candidate = shutil.which(executable)
    if path_candidate:
        return path_candidate
    raise RuntimeError(
        "SUMO was not found. Install Eclipse SUMO and either add its bin directory to PATH "
        "or set SUMO_HOME to the SUMO installation directory."
    )


def load_traci() -> Any:
    """Import TraCI after SUMO location checks so non-SUMO tests remain dependency-free."""
    try:
        import traci
    except ImportError as error:
        raise RuntimeError(
            "TraCI is unavailable. Install Eclipse SUMO or install the Python 'traci' package."
        ) from error
    return traci


def build_sumo_command(binary: str, config_path: Path, seed: int) -> list[str]:
    return [binary, "-c", str(config_path), "--seed", str(seed), "--start", "--quit-on-end"]


def is_parked(traci: Any, vehicle_id: str) -> bool:
    """Parking-area state is the primary label; stopped state is retained as a fallback proxy."""
    if traci.vehicle.isStoppedParking(vehicle_id):
        return True
    return bool(traci.vehicle.isStopped(vehicle_id) and traci.vehicle.getStopState(vehicle_id) & 2)


def write_dataset(
    traci: Any,
    output_path: Path,
    rng: random.Random,
    beacons: tuple[tuple[float, float], ...] = BEACON_POSITIONS_METERS,
) -> int:
    """Advance a running TraCI session and write one sensor record per active vehicle per step."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    previous_speeds: dict[str, float] = {}
    row_count = 0

    with output_path.open("w", newline="", encoding="utf-8") as dataset_file:
        writer = csv.DictWriter(dataset_file, fieldnames=DATASET_COLUMNS)
        writer.writeheader()
        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()
            timestep = int(traci.simulation.getTime())
            for vehicle_id in sorted(traci.vehicle.getIDList()):
                x_position, y_position = traci.vehicle.getPosition(vehicle_id)
                latitude, longitude = sumo_coords_to_wgs84(x_position, y_position)
                speed_mps = traci.vehicle.getSpeed(vehicle_id)
                nearest_distance = nearest_beacon_distance((x_position, y_position), beacons)
                writer.writerow(
                    {
                        "vehicle_id": vehicle_id,
                        "timestep": timestep,
                        "lat": f"{latitude:.7f}",
                        "lon": f"{longitude:.7f}",
                        "gps_speed": f"{derive_gps_speed(speed_mps, rng):.4f}",
                        "ble_rssi": f"{derive_ble_rssi(nearest_distance, rng):.4f}",
                        "imu_magnitude": f"{derive_imu_magnitude(speed_mps, previous_speeds.get(vehicle_id, speed_mps), 1.0, rng):.4f}",
                        "label": "parked" if is_parked(traci, vehicle_id) else "moving",
                    }
                )
                previous_speeds[vehicle_id] = speed_mps
                row_count += 1
    return row_count


def run_simulation(config_path: Path, output_path: Path, seed: int, gui: bool = False) -> int:
    if not config_path.is_file():
        raise FileNotFoundError(f"SUMO configuration does not exist: {config_path}")

    traci = load_traci()
    traci.start(build_sumo_command(find_sumo_binary(gui), config_path, seed))
    try:
        return write_dataset(traci, output_path, random.Random(seed))
    finally:
        traci.close()


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a labeled vehicle sensor dataset from SUMO.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH, help="Path to a SUMO .sumocfg file.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH, help="Destination CSV path.")
    parser.add_argument("--seed", type=int, default=20260918, help="Random seed for SUMO and sensor noise.")
    parser.add_argument("--gui", action="store_true", help="Run through sumo-gui instead of headless SUMO.")
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    try:
        row_count = run_simulation(arguments.config, arguments.output, arguments.seed, arguments.gui)
    except (FileNotFoundError, RuntimeError) as error:
        print(f"Simulation failed: {error}", file=sys.stderr)
        return 1
    print(f"Wrote {row_count} observations to {arguments.output}")
    return 0


if __name__ == "__main__":
    import sys
    from pathlib import Path

    # Add backend directory to Python path so 'app' can be imported as a module
    backend_dir = Path(__file__).resolve().parents[1]
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))

    raise SystemExit(main())
