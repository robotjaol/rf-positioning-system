from __future__ import annotations

import math

from .geo import weighted_lla
from .schemas import CellObservation, WifiObservation
from .storage import Storage


class FingerprintEngine:
    def __init__(self, storage: Storage) -> None:
        self.storage = storage

    def learn(self, latitude_deg: float, longitude_deg: float, altitude_m: float, wifi: list[WifiObservation], cells: list[CellObservation]) -> None:
        for ap in wifi:
            self.storage.update_anchor("wifi", ap.bssid.lower(), latitude_deg, longitude_deg, altitude_m)
        for cell in cells:
            self.storage.update_anchor("cell", cell.key, latitude_deg, longitude_deg, altitude_m)

    def estimate_wifi(self, wifi: list[WifiObservation]) -> tuple[tuple[float, float, float], float, int] | None:
        points: list[tuple[float, float, float]] = []
        weights: list[float] = []
        for ap in wifi:
            row = self.storage.get_anchor("wifi", ap.bssid.lower())
            if row is None:
                continue
            points.append((row["latitude_deg"], row["longitude_deg"], row["altitude_m"]))
            weights.append(max(0.05, math.exp((ap.rssi_dbm + 80) / 12.0)))
        if not points:
            return None
        sigma = max(8.0, 35.0 / math.sqrt(len(points)))
        return weighted_lla(points, weights), sigma, len(points)

    def estimate_cell(self, cells: list[CellObservation]) -> tuple[tuple[float, float, float], float, int] | None:
        points: list[tuple[float, float, float]] = []
        weights: list[float] = []
        for cell in cells:
            row = self.storage.get_anchor("cell", cell.key)
            if row is None:
                continue
            points.append((row["latitude_deg"], row["longitude_deg"], row["altitude_m"]))
            signal = cell.signal_dbm if cell.signal_dbm is not None else -110
            weights.append(max(0.05, math.exp((signal + 115) / 18.0)) * (1.4 if cell.registered else 1.0))
        if not points:
            return None
        sigma = max(25.0, 120.0 / math.sqrt(len(points)))
        return weighted_lla(points, weights), sigma, len(points)
