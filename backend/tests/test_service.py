from pathlib import Path

from app.schemas import ImuSample, LocationFix, TelemetryPacket, WifiObservation
from app.service import PositioningService
from app.storage import Storage


def test_end_to_end_gnss_then_wifi_fallback(tmp_path: Path) -> None:
    service = PositioningService(Storage(tmp_path / "test.sqlite3"))
    first = TelemetryPacket(
        device_id="phone", timestamp_ms=1_000,
        location=LocationFix(latitude_deg=-7.2756, longitude_deg=112.7932, altitude_m=10, accuracy_m=4),
        wifi=[WifiObservation(bssid="aa:bb:cc:dd:ee:ff", rssi_dbm=-45)],
    )
    assert service.ingest(first) is not None
    second = TelemetryPacket(
        device_id="phone", timestamp_ms=2_000,
        imu=ImuSample(accel_enu_mps2=(0.0, 0.0, 0.0)),
        wifi=[WifiObservation(bssid="aa:bb:cc:dd:ee:ff", rssi_dbm=-48)],
    )
    estimate = service.ingest(second)
    assert estimate is not None
    assert estimate.source == "wifi"
    assert estimate.wifi_matches == 1
