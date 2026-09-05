# Telemetry protocol

`POST /v1/telemetry` accepts one JSON packet per sample. The Android client sends at approximately 1 Hz while the foreground activity is running.

Minimum packet:

```json
{"device_id":"phone","timestamp_ms":0,"wifi":[],"cells":[],"gnss_raw":[]}
```

A useful packet includes an Android location fix, ENU acceleration, Wi-Fi observations, cell observations and raw GNSS measurements. All fields that depend on device capabilities are optional.

The API returns the current fused estimate after ingestion. Before the first absolute location fix, it returns JSON `null` because no geographic origin exists yet.

`GET /v1/devices` lists devices that have produced position estimates. `GET /v1/positions/{device_id}` returns recent fused positions. `/ws` broadcasts new fused estimates to connected dashboard clients.
