from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ParkingZone(Base):
    """
    Geographic bounding partition representing a parking zone in the spatial grid.
    Supports structured (dedicated parking lots) and unstructured (curbside/on-street) zones.
    """

    __tablename__ = "parking_zones"

    zone_id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    lat_min: Mapped[float] = mapped_column(Float, nullable=False)
    lat_max: Mapped[float] = mapped_column(Float, nullable=False)
    lon_min: Mapped[float] = mapped_column(Float, nullable=False)
    lon_max: Mapped[float] = mapped_column(Float, nullable=False)
    zone_type: Mapped[str] = mapped_column(String(32), nullable=False, default="unstructured")
    name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    total_capacity: Mapped[int] = mapped_column(Integer, default=10)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    readings: Mapped[list["VehicleReading"]] = relationship(
        "VehicleReading", back_populates="zone", cascade="all, delete-orphan"
    )


class VehicleReading(Base):
    """
    Ingested sensor telemetry and model classification reading for a vehicle.
    """

    __tablename__ = "vehicle_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vehicle_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True, nullable=False
    )
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    predicted_state: Mapped[str] = mapped_column(String(16), nullable=False)
    zone_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("parking_zones.zone_id", ondelete="SET NULL"), nullable=True, index=True
    )
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    gps_speed: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ble_rssi: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    imu_magnitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    zone: Mapped[Optional["ParkingZone"]] = relationship("ParkingZone", back_populates="readings")


class ParkingObservation(Base):
    """A normalized availability observation linked to a spatial grid cell."""

    __tablename__ = "parking_observations"

    id: Mapped[int] = mapped_column(primary_key=True)
    grid_cell_id: Mapped[str] = mapped_column(String(64), index=True)
    occupancy_probability: Mapped[float] = mapped_column(Float)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

