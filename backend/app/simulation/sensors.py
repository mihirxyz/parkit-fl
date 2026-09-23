from __future__ import annotations

import math
import random
from collections.abc import Sequence

GPS_SPEED_NOISE_STDDEV_METERS_PER_SECOND = 0.35
BLE_REFERENCE_RSSI_DBM = -45.0
BLE_PATH_LOSS_EXPONENT = 2.2
BLE_RSSI_NOISE_STDDEV_DB = 2.0
IMU_NOISE_STDDEV_METERS_PER_SECOND_SQUARED = 0.08


def euclidean_distance(point: tuple[float, float], beacon: tuple[float, float]) -> float:
    return math.hypot(point[0] - beacon[0], point[1] - beacon[1])


def nearest_beacon_distance(
    position: tuple[float, float], beacons: Sequence[tuple[float, float]]
) -> float:
    if not beacons:
        raise ValueError("at least one beacon is required")
    return min(euclidean_distance(position, beacon) for beacon in beacons)


def derive_gps_speed(speed_mps: float, rng: random.Random) -> float:
    """Return a non-negative GPS-like speed measurement in metres per second."""
    return max(0.0, speed_mps + rng.gauss(0.0, GPS_SPEED_NOISE_STDDEV_METERS_PER_SECOND))


def derive_ble_rssi(distance_meters: float, rng: random.Random) -> float:
    """Use a log-distance path-loss model to simulate nearest-beacon RSSI in dBm."""
    if distance_meters < 0:
        raise ValueError("distance_meters cannot be negative")
    effective_distance = max(distance_meters, 1.0)
    rssi = BLE_REFERENCE_RSSI_DBM - 10 * BLE_PATH_LOSS_EXPONENT * math.log10(effective_distance)
    return rssi + rng.gauss(0.0, BLE_RSSI_NOISE_STDDEV_DB)


def derive_imu_magnitude(
    current_speed_mps: float, previous_speed_mps: float, step_seconds: float, rng: random.Random
) -> float:
    """Approximate longitudinal acceleration magnitude with a small sensor-noise floor."""
    if step_seconds <= 0:
        raise ValueError("step_seconds must be positive")
    acceleration = abs(current_speed_mps - previous_speed_mps) / step_seconds
    return max(0.0, acceleration + rng.gauss(0.0, IMU_NOISE_STDDEV_METERS_PER_SECOND_SQUARED))
