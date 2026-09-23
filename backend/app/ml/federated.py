from collections.abc import Mapping, Sequence

import torch

StateDict = Mapping[str, torch.Tensor]


def federated_average(weighted_updates: Sequence[tuple[StateDict, int]]) -> dict[str, torch.Tensor]:
    """Aggregate compatible client model states using sample-count weighted FedAvg."""
    if not weighted_updates:
        raise ValueError("at least one client update is required")

    reference_keys = set(weighted_updates[0][0])
    if not reference_keys:
        raise ValueError("client model states cannot be empty")

    total_samples = sum(sample_count for _, sample_count in weighted_updates)
    if total_samples <= 0:
        raise ValueError("total sample count must be positive")

    aggregated: dict[str, torch.Tensor] = {}
    for state, sample_count in weighted_updates:
        if set(state) != reference_keys:
            raise ValueError("all client model states must have identical parameter keys")
        if sample_count < 0:
            raise ValueError("sample counts cannot be negative")

    for key in reference_keys:
        accumulator = torch.zeros_like(weighted_updates[0][0][key], dtype=torch.float32)
        for state, sample_count in weighted_updates:
            accumulator += state[key].detach().to(torch.float32) * (sample_count / total_samples)
        aggregated[key] = accumulator

    return aggregated
