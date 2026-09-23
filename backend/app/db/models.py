from datetime import datetime

from sqlalchemy import DateTime, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ParkingObservation(Base):
    """A normalized availability observation linked to a spatial grid cell."""

    __tablename__ = "parking_observations"

    id: Mapped[int] = mapped_column(primary_key=True)
    grid_cell_id: Mapped[str] = mapped_column(String(64), index=True)
    occupancy_probability: Mapped[float] = mapped_column(Float)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
