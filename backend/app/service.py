from __future__ import annotations

from dataclasses import dataclass

from .ekf import PositionEkf
from .fingerprint import FingerprintEngine
from .geo import enu_to_lla, lla_to_enu
from .schemas import FusedEstimate, TelemetryPacket
from .storage import Storage


@dataclass
class DeviceState:
    origin: tuple[float, float, float]
    filter: PositionEkf
    last_timestamp_ms: int


class PositioningService:
    def __init__(self, storage: Storage) -> None:
        self.storage = storage
        self.fingerprints = FingerprintEngine(storage)
        self.states: dict[str, DeviceState] = {}

    def ingest(self, packet: TelemetryPacket) -> FusedEstimate | None:
        self.storage.store_packet(packet.device_id, packet.timestamp_ms, packet.model_dump(mode="json"))
        state = self.states.get(packet.device_id)

        if state is None:
            if packet.location is None:
                return None
            altitude = packet.location.altitude_m or 0.0
            state = DeviceState(
                origin=(packet.location.latitude_deg, packet.location.longitude_deg, altitude),
                filter=PositionEkf(),
                last_timestamp_ms=packet.timestamp_ms,
            )
            self.states[packet.device_id] = state

        dt_s = max(0.0, (packet.timestamp_ms - state.last_timestamp_ms) / 1000.0)
        accel = packet.imu.accel_enu_mps2 if packet.imu else None
        state.filter.predict(dt_s, accel)
        state.last_timestamp_ms = packet.timestamp_ms

        sources: list[str] = []
        wifi_matches = 0
        cell_matches = 0

        if packet.location is not None:
            alt = packet.location.altitude_m if packet.location.altitude_m is not None else state.origin[2]
            gnss_enu = lla_to_enu(packet.location.latitude_deg, packet.location.longitude_deg, alt, state.origin)
            state.filter.update_position(gnss_enu, packet.location.accuracy_m)
            sources.append("gnss")
            if packet.location.accuracy_m <= 15.0:
                self.fingerprints.learn(packet.location.latitude_deg, packet.location.longitude_deg, alt, packet.wifi, packet.cells)
        else:
            wifi_est = self.fingerprints.estimate_wifi(packet.wifi)
            if wifi_est is not None:
                lla, sigma, wifi_matches = wifi_est
                state.filter.update_position(lla_to_enu(*lla, state.origin), sigma)
                sources.append("wifi")
            cell_est = self.fingerprints.estimate_cell(packet.cells)
            if cell_est is not None:
                lla, sigma, cell_matches = cell_est
                state.filter.update_position(lla_to_enu(*lla, state.origin), sigma)
                sources.append("cell")

        east, north, up = state.filter.position
        lat, lon, alt = enu_to_lla(east, north, up, state.origin)
        if not sources:
            source = "dead_reckoning"
        elif len(sources) == 1:
            source = sources[0]
        else:
            source = "mixed"

        estimate = FusedEstimate(
            device_id=packet.device_id,
            timestamp_ms=packet.timestamp_ms,
            latitude_deg=lat,
            longitude_deg=lon,
            altitude_m=alt,
            horizontal_sigma_m=state.filter.horizontal_sigma_m,
            source=source,
            gnss_available=packet.location is not None,
            wifi_matches=wifi_matches,
            cell_matches=cell_matches,
        )
        self.storage.store_position(estimate.model_dump())
        return estimate
