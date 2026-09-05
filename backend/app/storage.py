from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any


class Storage:
    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        with self._conn:
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS packets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT NOT NULL,
                    timestamp_ms INTEGER NOT NULL,
                    payload_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_packets_device_ts ON packets(device_id, timestamp_ms);

                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT NOT NULL,
                    timestamp_ms INTEGER NOT NULL,
                    latitude_deg REAL NOT NULL,
                    longitude_deg REAL NOT NULL,
                    altitude_m REAL,
                    horizontal_sigma_m REAL NOT NULL,
                    source TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_positions_device_ts ON positions(device_id, timestamp_ms);

                CREATE TABLE IF NOT EXISTS anchors (
                    kind TEXT NOT NULL,
                    anchor_key TEXT NOT NULL,
                    latitude_deg REAL NOT NULL,
                    longitude_deg REAL NOT NULL,
                    altitude_m REAL NOT NULL,
                    samples INTEGER NOT NULL,
                    PRIMARY KEY(kind, anchor_key)
                );
                """
            )

    def store_packet(self, device_id: str, timestamp_ms: int, payload: dict[str, Any]) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT INTO packets(device_id,timestamp_ms,payload_json) VALUES(?,?,?)",
                (device_id, timestamp_ms, json.dumps(payload, separators=(",", ":"))),
            )

    def store_position(self, estimate: dict[str, Any]) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                """INSERT INTO positions(device_id,timestamp_ms,latitude_deg,longitude_deg,altitude_m,horizontal_sigma_m,source)
                   VALUES(?,?,?,?,?,?,?)""",
                (
                    estimate["device_id"], estimate["timestamp_ms"], estimate["latitude_deg"],
                    estimate["longitude_deg"], estimate.get("altitude_m"), estimate["horizontal_sigma_m"],
                    estimate["source"],
                ),
            )

    def update_anchor(self, kind: str, key: str, lat: float, lon: float, alt: float) -> None:
        with self._lock, self._conn:
            row = self._conn.execute(
                "SELECT latitude_deg,longitude_deg,altitude_m,samples FROM anchors WHERE kind=? AND anchor_key=?",
                (kind, key),
            ).fetchone()
            if row is None:
                self._conn.execute(
                    "INSERT INTO anchors(kind,anchor_key,latitude_deg,longitude_deg,altitude_m,samples) VALUES(?,?,?,?,?,1)",
                    (kind, key, lat, lon, alt),
                )
                return
            n = int(row["samples"])
            n2 = n + 1
            self._conn.execute(
                """UPDATE anchors SET latitude_deg=?,longitude_deg=?,altitude_m=?,samples=?
                   WHERE kind=? AND anchor_key=?""",
                (
                    (row["latitude_deg"] * n + lat) / n2,
                    (row["longitude_deg"] * n + lon) / n2,
                    (row["altitude_m"] * n + alt) / n2,
                    n2, kind, key,
                ),
            )

    def get_anchor(self, kind: str, key: str) -> sqlite3.Row | None:
        with self._lock:
            return self._conn.execute(
                "SELECT * FROM anchors WHERE kind=? AND anchor_key=?", (kind, key)
            ).fetchone()

    def devices(self) -> list[str]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT device_id, MAX(timestamp_ms) ts FROM positions GROUP BY device_id ORDER BY ts DESC"
            ).fetchall()
        return [str(r["device_id"]) for r in rows]

    def positions(self, device_id: str, limit: int) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                """SELECT device_id,timestamp_ms,latitude_deg,longitude_deg,altitude_m,horizontal_sigma_m,source
                   FROM positions WHERE device_id=? ORDER BY timestamp_ms DESC LIMIT ?""",
                (device_id, limit),
            ).fetchall()
        return [dict(r) for r in reversed(rows)]
