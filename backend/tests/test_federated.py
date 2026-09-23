import pytest
import torch

from app.ml.federated import federated_average


def test_federated_average_weights_updates_by_sample_count() -> None:
    result = federated_average(
        [
            ({"weight": torch.tensor([1.0, 3.0])}, 1),
            ({"weight": torch.tensor([4.0, 6.0])}, 3),
        ]
    )

    assert torch.allclose(result["weight"], torch.tensor([3.25, 5.25]))


def test_federated_average_rejects_empty_updates() -> None:
    with pytest.raises(ValueError, match="at least one"):
        federated_average([])
