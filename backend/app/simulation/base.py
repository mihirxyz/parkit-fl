from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class SimulatedObservation:
    latitude: float
    longitude: float
    occupancy_probability: float
    observed_at: datetime


class SimulationAdapter(Protocol):
    """Boundary implemented by integrations with external mobility simulators."""

    def collect_observations(self) -> list[SimulatedObservation]:
        """Return normalized observations from one simulation step."""
