"""
Virtual Fence — FastAPI Application
Single-service backend: REST API, MJPEG streaming, WebSocket telemetry,
and static-file SPA hosting for the Next.js frontend.
"""

import asyncio
import json
import os
import threading
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import List, Optional, Dict

import cv2
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import Base, engine, get_db
from backend.models import ZoneModel, IncidentModel
from backend.vision_engine import VirtualFenceEngine, SyntheticVideoSource

# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------
_engines: Dict[int, VirtualFenceEngine] = {}
_video_captures: Dict[int, object] = {}
_processing_threads: List[threading.Thread] = []
_shutdown_event = threading.Event()
_ws_clients: List[WebSocket] = []

# Camera management
_available_cameras: List[dict] = []
_cameras_lock = threading.Lock()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_BACKEND_DIR)
_FRONTEND_OUT = os.path.join(_PROJECT_ROOT, "frontend", "out")
_SNAPSHOTS_DIR = os.path.join(_BACKEND_DIR, "storage", "snapshots")
_VIDEOS_DIR = os.path.join(_BACKEND_DIR, "storage", "videos")
os.makedirs(_SNAPSHOTS_DIR, exist_ok=True)
os.makedirs(_VIDEOS_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Background vision processing
# ---------------------------------------------------------------------------
def _open_camera(index: int):
    """Open camera by index; falls back to SyntheticVideoSource if unavailable."""
    try:
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            # Test-read: some Windows cameras report isOpened=True but never produce frames
            ret, frame = cap.read()
            if ret and frame is not None and frame.size > 0:
                print(f"[Virtual Fence] Camera {index} opened and verified (test frame OK).")
                return cap
            else:
                print(f"[Virtual Fence] Camera {index} opened but test frame failed — skipping.")
        cap.release()
    except Exception as e:
        print(f"[Virtual Fence] Camera {index} error: {e}")
    print(f"[Virtual Fence] Camera {index} unavailable — falling back to synthetic feed.")
    return SyntheticVideoSource()

def _vision_loop(camera_index: int, camera_name: str) -> None:
    """Runs in a daemon thread — reads and processes frames for a specific camera."""
    cap = _open_camera(camera_index)
    _video_captures[camera_index] = cap
    
    vision_engine = VirtualFenceEngine(camera_index, camera_name)
    vision_engine.reload_zones()
    _engines[camera_index] = vision_engine

    failed_reads = 0
    while not _shutdown_event.is_set():
        ret, frame = cap.read()
        if not ret or frame is None or frame.size == 0:
            failed_reads += 1
            if failed_reads > 30:
                print(f"[Virtual Fence] Camera {camera_index} stalled — falling back to synthetic feed.")
                cap.release()
                cap = SyntheticVideoSource()
                _video_captures[camera_index] = cap
                failed_reads = 0
            time.sleep(0.033)
            continue
            
        failed_reads = 0
        vision_engine.process_frame(frame)

    cap.release()
    print(f"[Virtual Fence] Vision loop stopped for camera {camera_index}.")

# ---------------------------------------------------------------------------
# WebSocket broadcaster (runs as async task)
# ---------------------------------------------------------------------------
async def _ws_broadcaster() -> None:
    """Periodically pushes telemetry + queued alerts to all connected WS clients."""
    while True:
        await asyncio.sleep(0.1)  # 10 Hz

        # Gather payload
        payload = {
            "active_targets": sum(e.telemetry["active_targets"] for e in _engines.values()),
            "state": "BREACH" if any(e.telemetry["state"] == "BREACH" for e in _engines.values()) else "SECURE",
            "cameras": [e.telemetry for e in _engines.values()]
        }

        # Attach any pending breach alerts
        alerts = []
        for engine_instance in _engines.values():
            while engine_instance.pending_events:
                alerts.append(engine_instance.pending_events.pop(0))
                
        if alerts:
            payload["alerts"] = alerts

        data = json.dumps(payload)

        # Broadcast
        stale: List[WebSocket] = []
        for ws in _ws_clients:
            try:
                await ws.send_text(data)
            except Exception:
                stale.append(ws)
        for ws in stale:
            try:
                _ws_clients.remove(ws)
            except ValueError:
                pass

# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    print("[Virtual Fence] Database tables ensured.")

    # Enumerate available cameras (test-read to verify they actually produce frames)
    cameras: List[dict] = []
    for i in range(6):
        try:
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None and frame.size > 0:
                    cameras.append({"index": i, "name": f"Camera {i}", "label": f"CAM-{i:02d}"})
                    print(f"[Virtual Fence] Camera {i} verified (test frame OK).")
                else:
                    print(f"[Virtual Fence] Camera {i} opened but produced no frame — skipping.")
            cap.release()
        except Exception:
            pass
            
    global _available_cameras
    _available_cameras = cameras if cameras else [{"index": 0, "name": "Default Camera", "label": "CAM-00"}]
    print(f"[Virtual Fence] Camera enumeration complete — {len(_available_cameras)} device(s) found.")

    # Spawn threads for all cameras
    for cam in _available_cameras:
        t = threading.Thread(target=_vision_loop, args=(cam["index"], cam["label"]), daemon=True)
        t.start()
        _processing_threads.append(t)

    broadcaster = asyncio.create_task(_ws_broadcaster())
    print("[Virtual Fence] System online — http://localhost:8000")

    yield

    # Shutdown
    _shutdown_event.set()
    broadcaster.cancel()
    for t in _processing_threads:
        t.join(timeout=3)
    print("[Virtual Fence] Shutdown complete.")

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Virtual Fence",
    version="1.0.0",
    description="Enterprise Autonomous Perimeter Intrusion & Spatial Boundary System",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------
class ZoneCreate(BaseModel):
    name: str
    type: str = "POLYGON"
    points: list  # [[x,y], …] normalised to [0,1]

class ZoneOut(BaseModel):
    id: str
    name: str
    type: str
    points: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class IncidentPatch(BaseModel):
    status: str  # ACKNOWLEDGED | RESOLVED

class IncidentOut(BaseModel):
    id: str
    zone_id: str
    object_id: int
    timestamp: datetime
    snapshot_path: str | None
    video_path: str | None
    status: str

    class Config:
        from_attributes = True

# ---------------------------------------------------------------------------
# REST API — Zones
# ---------------------------------------------------------------------------
@app.get("/api/v1/zones", response_model=List[ZoneOut])
def list_zones(db: Session = Depends(get_db)):
    return db.query(ZoneModel).order_by(ZoneModel.created_at.desc()).all()

@app.post("/api/v1/zones", response_model=ZoneOut, status_code=201)
def create_zone(payload: ZoneCreate, db: Session = Depends(get_db)):
    zone = ZoneModel(
        name=payload.name,
        type=payload.type,
        points=json.dumps(payload.points),
        is_active=True,
    )
    db.add(zone)
    db.commit()
    db.refresh(zone)
    for engine_instance in _engines.values():
        engine_instance.reload_zones()
    return zone

@app.delete("/api/v1/zones/{zone_id}", status_code=204)
def delete_zone(zone_id: str, db: Session = Depends(get_db)):
    zone = db.query(ZoneModel).filter(ZoneModel.id == zone_id).first()
    if not zone:
        raise HTTPException(404, "Zone not found")
    db.delete(zone)
    db.commit()
    for engine_instance in _engines.values():
        engine_instance.reload_zones()
    return None

# ---------------------------------------------------------------------------
# REST API — Incidents
# ---------------------------------------------------------------------------
@app.get("/api/v1/incidents", response_model=List[IncidentOut])
def list_incidents(db: Session = Depends(get_db)):
    return (
        db.query(IncidentModel)
        .order_by(IncidentModel.timestamp.desc())
        .limit(100)
        .all()
    )

@app.patch("/api/v1/incidents/{incident_id}", response_model=IncidentOut)
def patch_incident(incident_id: str, payload: IncidentPatch, db: Session = Depends(get_db)):
    incident = db.query(IncidentModel).filter(IncidentModel.id == incident_id).first()
    if not incident:
        raise HTTPException(404, "Incident not found")
    if payload.status not in ("ACKNOWLEDGED", "RESOLVED"):
        raise HTTPException(400, "Status must be ACKNOWLEDGED or RESOLVED")
    incident.status = payload.status
    db.commit()
    db.refresh(incident)
    return incident

# ---------------------------------------------------------------------------
# Camera API
# ---------------------------------------------------------------------------
@app.get("/api/v1/cameras")
def list_cameras():
    return _available_cameras

# ---------------------------------------------------------------------------
# MJPEG Streaming
# ---------------------------------------------------------------------------
def _mjpeg_generator(camera_index: int):
    while True:
        engine_instance = _engines.get(camera_index)
        if engine_instance and engine_instance.latest_jpeg:
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + engine_instance.latest_jpeg + b"\r\n"
            )
        time.sleep(0.033)

@app.get("/api/v1/video_feed/{camera_index}")
def video_feed(camera_index: int):
    if camera_index not in _engines:
        raise HTTPException(404, "Camera not found")
    return StreamingResponse(
        _mjpeg_generator(camera_index),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )

@app.get("/api/v1/video_feed")
def video_feed_default():
    if not _engines:
        raise HTTPException(404, "No cameras available")
    first_cam = list(_engines.keys())[0]
    return StreamingResponse(
        _mjpeg_generator(first_cam),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )

# ---------------------------------------------------------------------------
# WebSocket Telemetry
# ---------------------------------------------------------------------------
@app.websocket("/ws/telemetry")
async def ws_telemetry(websocket: WebSocket):
    await websocket.accept()
    _ws_clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        try:
            _ws_clients.remove(websocket)
        except ValueError:
            pass

# ---------------------------------------------------------------------------
# Static mounts
# ---------------------------------------------------------------------------
app.mount("/snapshots", StaticFiles(directory=_SNAPSHOTS_DIR), name="snapshots")
app.mount("/videos", StaticFiles(directory=_VIDEOS_DIR), name="videos")

# ---------------------------------------------------------------------------
# SPA catch-all
# ---------------------------------------------------------------------------
if os.path.isdir(_FRONTEND_OUT):
    @app.api_route("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        if full_path.startswith("api/") or full_path.startswith("ws/") or full_path.startswith("snapshots/") or full_path.startswith("videos/"):
            raise HTTPException(status_code=404, detail="Not Found")

        file_path = os.path.join(_FRONTEND_OUT, full_path)
        if os.path.isfile(file_path):
            from fastapi.responses import FileResponse
            return FileResponse(file_path)

        html_file = os.path.join(_FRONTEND_OUT, f"{full_path}.html")
        if os.path.isfile(html_file):
            return HTMLResponse(content=open(html_file, "r", encoding="utf-8").read())

        sub_index = os.path.join(_FRONTEND_OUT, full_path, "index.html")
        if os.path.isfile(sub_index):
            return HTMLResponse(content=open(sub_index, "r", encoding="utf-8").read())

        fallback_path = os.path.join(_FRONTEND_OUT, "index.html")
        if os.path.isfile(fallback_path):
            return HTMLResponse(content=open(fallback_path, "r", encoding="utf-8").read())
        
        raise HTTPException(status_code=404, detail="Page not found")

    app.mount("/", StaticFiles(directory=_FRONTEND_OUT, html=True), name="spa")
    print(f"[Virtual Fence] SPA static files mounted from {_FRONTEND_OUT}")
else:
    @app.get("/")
    def _fallback_root():
        return HTMLResponse(
            "<html><body style='background:#0f172a;color:#e2e8f0;font-family:sans-serif;'>"
            "<div style='text-align:center'><h1>Virtual Fence API</h1></div></body></html>"
        )
