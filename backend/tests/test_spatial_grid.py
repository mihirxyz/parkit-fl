import pytest

from app.grid.spatial import SpatialGrid


def test_grid_locate_returns_stable_identifier() -> None:
    grid = SpatialGrid(cell_size_degrees=0.01)

    cell = grid.locate(latitude=10.005, longitude=20.005)

    assert cell.identifier == "cell:10000:20000"


@pytest.mark.parametrize("latitude, longitude", [(91, 0), (-91, 0), (0, 181), (0, -181)])
def test_grid_rejects_invalid_coordinates(latitude: float, longitude: float) -> None:
    grid = SpatialGrid(cell_size_degrees=0.01)

    with pytest.raises(ValueError):
        grid.locate(latitude=latitude, longitude=longitude)
