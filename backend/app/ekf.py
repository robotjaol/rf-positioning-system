from __future__ import annotations

import numpy as np


class PositionEkf:
    """Six-state constant-acceleration EKF in a local ENU frame."""

    def __init__(self) -> None:
        self.x = np.zeros(6, dtype=float)
        self.p = np.diag([100.0, 100.0, 100.0, 25.0, 25.0, 25.0])

    def predict(self, dt_s: float, accel_enu_mps2: tuple[float, float, float] | None) -> None:
        dt = max(0.0, min(float(dt_s), 5.0))
        if dt == 0.0:
            return
        f = np.eye(6)
        f[0:3, 3:6] = np.eye(3) * dt
        a = np.asarray(accel_enu_mps2 or (0.0, 0.0, 0.0), dtype=float)
        b = np.zeros((6, 3))
        b[0:3, :] = np.eye(3) * 0.5 * dt * dt
        b[3:6, :] = np.eye(3) * dt
        self.x = f @ self.x + b @ a

        accel_noise = 1.8
        g = b
        q = g @ (np.eye(3) * accel_noise**2) @ g.T
        q += np.eye(6) * 1e-3
        self.p = f @ self.p @ f.T + q

    def update_position(self, position_enu_m: tuple[float, float, float], sigma_m: float) -> None:
        h = np.zeros((3, 6))
        h[:, 0:3] = np.eye(3)
        z = np.asarray(position_enu_m, dtype=float)
        r = np.eye(3) * max(float(sigma_m), 1.0) ** 2
        innovation = z - h @ self.x
        s = h @ self.p @ h.T + r
        k = self.p @ h.T @ np.linalg.inv(s)
        self.x = self.x + k @ innovation
        i = np.eye(6)
        self.p = (i - k @ h) @ self.p @ (i - k @ h).T + k @ r @ k.T

    @property
    def position(self) -> tuple[float, float, float]:
        return tuple(float(v) for v in self.x[:3])

    @property
    def horizontal_sigma_m(self) -> float:
        return float(np.sqrt(max(self.p[0, 0] + self.p[1, 1], 0.0) / 2.0))
