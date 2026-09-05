from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .schemas import FusedEstimate, TelemetryPacket
from .service import PositioningService
from .storage import Storage

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("RPS_DATA_DIR", BASE_DIR.parent / "data"))
storage = Storage(DATA_DIR / "positioning.sqlite3")
service = PositioningService(storage)

app = FastAPI(title="Resilient Positioning System", version="0.1.0")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
clients: set[WebSocket] = set()


@app.get("/")
def dashboard() -> FileResponse:
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/devices")
def devices() -> dict[str, list[str]]:
    return {"devices": storage.devices()}


@app.get("/v1/positions/{device_id}")
def positions(device_id: str, limit: int = 500) -> dict[str, object]:
    limit = max(1, min(limit, 5000))
    return {"device_id": device_id, "positions": storage.positions(device_id, limit)}


@app.post("/v1/telemetry", response_model=FusedEstimate | None)
async def telemetry(packet: TelemetryPacket) -> FusedEstimate | None:
    estimate = service.ingest(packet)
    if estimate is None:
        return None
    stale: list[WebSocket] = []
    for ws in list(clients):
        try:
            await ws.send_json(estimate.model_dump(mode="json"))
        except Exception:
            stale.append(ws)
    for ws in stale:
        clients.discard(ws)
    return estimate


@app.websocket("/ws")
async def websocket_feed(websocket: WebSocket) -> None:
    await websocket.accept()
    clients.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        clients.discard(websocket)
