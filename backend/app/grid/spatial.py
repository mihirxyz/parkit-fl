from dataclasses import dataclass
from math import floor


@dataclass(frozen=True)
class GridCell:
    row: int
    column: int

    @property
    def identifier(self) -> str:
        return f"cell:{self.row}:{self.column}"


class SpatialGrid:
    """Maps WGS84 coordinates to stable, fixed-size geographic grid cells."""

    def __init__(self, cell_size_degrees: float) -> None:
        if cell_size_degrees <= 0:
            raise ValueError("cell_size_degrees must be positive")
        self.cell_size_degrees = cell_size_degrees

    def locate(self, latitude: float, longitude: float) -> GridCell:
        if not -90 <= latitude <= 90:
            raise ValueError("latitude must be between -90 and 90")
        if not -180 <= longitude <= 180:
            raise ValueError("longitude must be between -180 and 180")
        return GridCell(
            row=floor((latitude + 90) / self.cell_size_degrees),
            column=floor((longitude + 180) / self.cell_size_degrees),
        )
