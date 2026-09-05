from __future__ import annotations

import math

EARTH_RADIUS_M = 6_378_137.0


def lla_to_enu(lat_deg: float, lon_deg: float, alt_m: float, origin: tuple[float, float, float]) -> tuple[float, float, float]:
    lat0_deg, lon0_deg, alt0_m = origin
    lat0 = math.radians(lat0_deg)
    east = math.radians(lon_deg - lon0_deg) * EARTH_RADIUS_M * math.cos(lat0)
    north = math.radians(lat_deg - lat0_deg) * EARTH_RADIUS_M
    up = alt_m - alt0_m
    return east, north, up


def enu_to_lla(east_m: float, north_m: float, up_m: float, origin: tuple[float, float, float]) -> tuple[float, float, float]:
    lat0_deg, lon0_deg, alt0_m = origin
    lat0 = math.radians(lat0_deg)
    lat = lat0_deg + math.degrees(north_m / EARTH_RADIUS_M)
    lon = lon0_deg + math.degrees(east_m / (EARTH_RADIUS_M * math.cos(lat0)))
    return lat, lon, alt0_m + up_m


def weighted_lla(points: list[tuple[float, float, float]], weights: list[float]) -> tuple[float, float, float]:
    total = sum(weights)
    if total <= 0:
        raise ValueError("weights must sum to a positive value")
    lat = sum(p[0] * w for p, w in zip(points, weights, strict=True)) / total
    lon = sum(p[1] * w for p, w in zip(points, weights, strict=True)) / total
    alt = sum(p[2] * w for p, w in zip(points, weights, strict=True)) / total
    return lat, lon, alt
