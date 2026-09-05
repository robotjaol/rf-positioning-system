#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import time
import urllib.request


def post(url: str, payload: dict) -> None:
    req = urllib.request.Request(
        url.rstrip("/") + "/v1/telemetry",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=3) as response:
        print(response.read().decode())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--speed", type=float, default=5.0, help="replay acceleration")
    args = parser.parse_args()
    base_lat, base_lon = -7.2756, 112.7932
    start = int(time.time() * 1000)
    for i in range(60):
        lat = base_lat + i * 0.00001
        lon = base_lon + math.sin(i / 8) * 0.00002
        gnss = i < 25 or i >= 45
        payload = {
            "device_id": "demo-phone",
            "timestamp_ms": start + i * 1000,
            "location": ({"latitude_deg": lat, "longitude_deg": lon, "altitude_m": 8.0, "accuracy_m": 4.5, "provider": "demo"} if gnss else None),
            "imu": {"accel_enu_mps2": [0.0, 0.0, 0.0], "gyro_rps": [0.0, 0.0, 0.0]},
            "wifi": [
                {"bssid": "02:00:00:00:00:01", "rssi_dbm": -45 - (i % 8), "frequency_mhz": 2412},
                {"bssid": "02:00:00:00:00:02", "rssi_dbm": -58 + (i % 5), "frequency_mhz": 5180}
            ],
            "cells": [{"key": "lte:510:10:100:200", "technology": "LTE", "signal_dbm": -91, "registered": True}],
            "gnss_raw": []
        }
        post(args.url, payload)
        time.sleep(max(0.01, 1.0 / args.speed))


if __name__ == "__main__":
    main()
