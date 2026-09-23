import random

import pytest

from app.simulation.sensors import (
    derive_ble_rssi,
    derive_gps_speed,
    derive_imu_magnitude,
    nearest_beacon_distance,
)


def test_nearest_beacon_distance_selects_closest_beacon() -> None:
    assert nearest_beacon_distance((3.0, 4.0), ((0.0, 0.0), (20.0, 20.0))) == 5.0


def test_sensor_features_are_reproducible_for_a_fixed_seed() -> None:
    first_rng = random.Random(7)
    second_rng = random.Random(7)

    first = (
        derive_gps_speed(10.0, first_rng),
        derive_ble_rssi(15.0, first_rng),
        derive_imu_magnitude(10.0, 8.0, 1.0, first_rng),
    )
    second = (
        derive_gps_speed(10.0, second_rng),
        derive_ble_rssi(15.0, second_rng),
        derive_imu_magnitude(10.0, 8.0, 1.0, second_rng),
    )

    assert first == second
    assert first[0] >= 0
    assert first[2] >= 0


@pytest.mark.parametrize("distance", [-1.0])
def test_ble_rssi_rejects_negative_distance(distance: float) -> None:
    with pytest.raises(ValueError, match="cannot be negative"):
        derive_ble_rssi(distance, random.Random(1))


def test_imu_magnitude_rejects_non_positive_step_duration() -> None:
    with pytest.raises(ValueError, match="must be positive"):
        derive_imu_magnitude(2.0, 1.0, 0.0, random.Random(1))
