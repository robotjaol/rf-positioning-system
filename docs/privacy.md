# Privacy and data handling

The system records location, nearby Wi-Fi BSSIDs, cellular identifiers and motion sensors. These observations can reveal where a device has been.

The default deployment is local: the Android client posts to a laptop endpoint and the backend stores data in a local SQLite file. No cloud service is required. Do not publish captured telemetry databases without reviewing them for sensitive location and network identifiers.

The repository contains no API keys, service credentials or proprietary positioning databases. Wi-Fi and cellular fallback learns anchors only from measurements collected by the user during operation.
