# Field experiment

Use one Android phone and one laptop on the same Wi-Fi network or phone hotspot.

1. Run the backend on the laptop and open `http://<laptop-ip>:8000`.
2. Install the Android app, grant precise location, enter the laptop endpoint and start streaming.
3. Walk an outdoor loop for at least five minutes with normal GNSS reception. This teaches local Wi-Fi and cell anchors.
4. Repeat the same loop. Introduce natural GNSS degradation by moving indoors or into covered areas. Do not disable location if you still want Wi-Fi scan results on Android versions that gate scanning behind location services.
5. Export the SQLite database or query `/v1/positions/{device_id}` for analysis.

## Metrics

When a trusted reference trajectory is available, report horizontal RMSE, median error, 95th percentile error and maximum outage duration. Compare at least these modes:

* GNSS fixes only
* EKF with GNSS and IMU propagation
* EKF with learned Wi-Fi fallback
* EKF with learned Wi-Fi and cellular fallback

Phone GNSS is not a survey-grade ground truth. For rigorous error claims, use an external reference such as RTK GNSS or a surveyed path. Without that reference, report continuity, internal covariance and repeatability rather than absolute accuracy.
