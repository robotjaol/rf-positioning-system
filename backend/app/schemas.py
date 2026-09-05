from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class LocationFix(BaseModel):
    latitude_deg: float
    longitude_deg: float
    altitude_m: float | None = None
    accuracy_m: float = Field(gt=0)
    speed_mps: float | None = None
    bearing_deg: float | None = None
    provider: str | None = None


class ImuSample(BaseModel):
    accel_enu_mps2: tuple[float, float, float] | None = None
    gyro_rps: tuple[float, float, float] | None = None
    pressure_hpa: float | None = None


class WifiObservation(BaseModel):
    bssid: str
    rssi_dbm: int
    frequency_mhz: int | None = None


class CellObservation(BaseModel):
    key: str
    technology: str
    signal_dbm: int | None = None
    registered: bool = False


class RawGnssMeasurement(BaseModel):
    svid: int
    constellation_type: int
    cn0_dbhz: float
    pseudorange_rate_mps: float | None = None
    accumulated_delta_range_m: float | None = None
    carrier_frequency_hz: float | None = None
    state: int | None = None


class GnssClockSample(BaseModel):
    time_nanos: int
    full_bias_nanos: int | None = None
    bias_nanos: float | None = None


class TelemetryPacket(BaseModel):
    device_id: str = Field(min_length=1, max_length=128)
    timestamp_ms: int
    location: LocationFix | None = None
    imu: ImuSample | None = None
    wifi: list[WifiObservation] = Field(default_factory=list)
    cells: list[CellObservation] = Field(default_factory=list)
    gnss_clock: GnssClockSample | None = None
    gnss_raw: list[RawGnssMeasurement] = Field(default_factory=list)


class FusedEstimate(BaseModel):
    device_id: str
    timestamp_ms: int
    latitude_deg: float
    longitude_deg: float
    altitude_m: float | None
    horizontal_sigma_m: float
    source: Literal["gnss", "wifi", "cell", "dead_reckoning", "mixed"]
    gnss_available: bool
    wifi_matches: int
    cell_matches: int
