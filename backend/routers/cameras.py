"""
Virtual Fence — Camera Router
Endpoints for camera listing, MJPEG streaming, snapshots, and WebSocket telemetry.
"""

import time
from typing import List

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import Response, StreamingResponse

from backend.exceptions import CameraNotAvailableError
from backend.schemas import CameraOut
from backend.services.camera_service import camera_manager

router = APIRouter(prefix="/api/v1", tags=["Cameras"])


@router.get("/cameras", response_model=List[CameraOut])
def list_cameras():
    """List all available camera devices."""
    return camera_manager.available_cameras


# ---------------------------------------------------------------------------
# MJPEG Streaming
# ---------------------------------------------------------------------------
def _mjpeg_generator(camera_index: int):
    while True:
        engine = camera_manager.engines.get(camera_index)
        if engine and engine.latest_jpeg:
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + engine.latest_jpeg + b"\r\n"
            )
        time.sleep(0.033)


@router.get("/video_feed/{camera_index}")
def video_feed(camera_index: int):
    """Stream MJPEG video from a specific camera."""
    if camera_index not in camera_manager.engines:
        raise CameraNotAvailableError(camera_index)

    camera_manager.set_active_camera(camera_index)

    return StreamingResponse(
        _mjpeg_generator(camera_index),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@router.get("/video_feed")
def video_feed_default():
    """Stream MJPEG video from the first available camera."""
    if not camera_manager.engines:
        raise HTTPException(404, "No cameras available")
    first_cam = list(camera_manager.engines.keys())[0]
    return StreamingResponse(
        _mjpeg_generator(first_cam),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


# ---------------------------------------------------------------------------
# Snapshots
# ---------------------------------------------------------------------------
@router.get("/snapshot/{camera_index}")
def get_snapshot(camera_index: int):
    """Get a JPEG snapshot from a specific camera."""
    engine = camera_manager.engines.get(camera_index)
    if not engine or not engine.latest_jpeg:
        raise HTTPException(503, "No frame available yet — camera may still be initialising.")
    return Response(
        content=engine.latest_jpeg,
        media_type="image/jpeg",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )


@router.get("/snapshot")
def get_snapshot_default():
    """Get a JPEG snapshot from the first available camera."""
    if not camera_manager.engines:
        raise HTTPException(503, "No cameras available")
    first_cam = list(camera_manager.engines.keys())[0]
    return get_snapshot(first_cam)


# ---------------------------------------------------------------------------
# WebSocket Telemetry
# ---------------------------------------------------------------------------
ws_router = APIRouter(tags=["WebSocket"])


@ws_router.websocket("/ws/telemetry")
async def ws_telemetry(websocket: WebSocket):
    """WebSocket endpoint for real-time telemetry streaming at 10Hz."""
    await websocket.accept()
    camera_manager.add_ws_client(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        camera_manager.remove_ws_client(websocket)
