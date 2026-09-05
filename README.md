# Resilient Positioning System

A phone-to-laptop positioning stack that collects GNSS, IMU, Wi-Fi and cellular observations on Android, fuses them on a laptop and displays the estimated trajectory in a live web interface.

The baseline is designed to run with two devices only: an Android phone and a laptop. It does not depend on Google or Apple positioning databases.

## Data path

```text
Android sensors
  GNSS fix + raw GNSS measurements
  linear acceleration + gyroscope + rotation vector
  Wi-Fi scan results
  cellular observations
        |
        v
HTTP telemetry
        |
        v
FastAPI ingestion -> SQLite archive
        |
        +-> local Wi-Fi / cell anchor learning
        |
        v
6-state ENU EKF
        |
        v
WebSocket -> live Leaflet dashboard
```

## Current behavior

* Uses Android GNSS fixes as absolute position measurements.
* Propagates position and velocity with device acceleration transformed to the Android world frame.
* Learns local Wi-Fi BSSID and cellular anchors only when GNSS accuracy is 15 m or better.
* Uses learned Wi-Fi and cellular observations as coarse corrections during GNSS outages.
* Records raw `GnssMeasurementsEvent` clock and per-satellite measurements for later raw-GNSS processing.
* Stores telemetry and fused positions in SQLite.
* Serves a live map and source/uncertainty status from the same backend.

Raw GNSS pseudorange positioning is not implemented in version 0.1. The measurements are archived, but the active estimator starts from Android location fixes. This keeps the first version reproducible on ordinary phones while leaving a clean path to a WLS/RTK extension.

## Laptop setup

Python 3.11 or newer is required.

```bash
git clone <repository-url>
cd resilient-positioning-system
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
make test
make run
```

Open `http://127.0.0.1:8000` on the laptop. For the phone, find the laptop's LAN IP and use an endpoint such as `http://192.168.1.10:8000`.

Docker is also supported:

```bash
docker compose up --build
```

## Android setup

Open `android/` in Android Studio. The project targets API 37 and uses Android Gradle Plugin 9.4.0 with Kotlin 2.3.21. Build and install the debug app on a physical Android phone.

Grant precise location access. Enter the laptop endpoint in the app and select **Start streaming**. The app runs as a foreground activity and sends one packet per second. Wi-Fi active scan requests are intentionally spaced by 30 seconds; Android may still throttle them.

The app uses cleartext HTTP for local LAN development. Do not expose this backend directly to the internet.

## Run without a phone

Start the backend, then replay the deterministic demo trace:

```bash
make run
# another terminal
python3 scripts/replay_demo.py --url http://127.0.0.1:8000
```

The demo supplies GNSS for the first part of the route, removes it for 20 seconds, then restores it. Learned Wi-Fi and cellular anchors exercise the fallback path.

## Repository layout

```text
android/               Android telemetry collector
backend/app/           API, storage, fingerprint engine and EKF
backend/tests/         estimator and end-to-end service tests
docs/                  architecture, protocol, field test and privacy notes
scripts/replay_demo.py synthetic end-to-end replay
research/               reserved for raw-GNSS notebooks and experiments
```

## Measurement limitations

Phone capabilities vary. Raw GNSS fields, barometer, telephony radio access and individual motion sensors may be missing. Android also rate-limits Wi-Fi scans. The collector treats these sources as optional instead of fabricating unavailable measurements.

The ENU conversion is a local tangent approximation and the IMU path inherits phone orientation, magnetic heading and sensor bias errors. Wi-Fi/cell fallback is a self-built local fingerprint, not a global geolocation service. Its accuracy depends on how densely the area has been learned and how stable the radio environment is.

## Documentation

* [Architecture](docs/architecture.md)
* [Telemetry protocol](docs/protocol.md)
* [Field experiment](docs/experiment.md)
* [Privacy](docs/privacy.md)
* [Verification record](docs/verification.md)

## License

MIT
