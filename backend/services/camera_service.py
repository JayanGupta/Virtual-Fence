"""
Virtual Fence — Camera Service
Camera enumeration, lifecycle management, and state tracking.
"""

import asyncio
import json
import threading
import time
from typing import Dict, List, Optional

import cv2
from fastapi import WebSocket

from backend.config import get_settings
from backend.logging_config import get_logger
from backend.vision_engine import VirtualFenceEngine, SyntheticVideoSource

logger = get_logger("services.cameras")


class CameraManager:
    """Manages camera lifecycle, vision engines, and WebSocket broadcasting."""

    def __init__(self) -> None:
        self.engines: Dict[int, VirtualFenceEngine] = {}
        self.video_captures: Dict[int, object] = {}
        self.processing_threads: List[threading.Thread] = []
        self.shutdown_event = threading.Event()
        self.ws_clients: List[WebSocket] = []
        self.available_cameras: List[dict] = []
        self.active_camera_index: int = 0
        self._cameras_lock = threading.Lock()

    def enumerate_cameras(self) -> List[dict]:
        """Detect and verify available camera devices."""
        settings = get_settings()
        cameras: List[dict] = []

        for i in range(settings.MAX_CAMERA_SCAN):
            try:
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None and frame.size > 0:
                        cameras.append({
                            "index": i,
                            "name": f"Camera {i}",
                            "label": f"CAM-{i:02d}",
                        })
                        logger.info("Camera %d verified (test frame OK)", i)
                    else:
                        logger.debug("Camera %d opened but produced no frame — skipping", i)
                cap.release()
            except Exception as e:
                logger.debug("Camera %d error during enumeration: %s", i, e)

        if not cameras:
            cameras = [{"index": 0, "name": "Default Camera", "label": "CAM-00"}]
            logger.info("No physical cameras found — using synthetic feed")

        self.available_cameras = cameras
        logger.info("Camera enumeration complete — %d device(s) found", len(cameras))
        return cameras

    def start_all(self) -> None:
        """Spawn vision processing threads for all detected cameras."""
        for cam in self.available_cameras:
            t = threading.Thread(
                target=self._vision_loop,
                args=(cam["index"], cam["label"]),
                daemon=True,
            )
            t.start()
            self.processing_threads.append(t)
            logger.info("Vision thread started for %s (camera %d)", cam["label"], cam["index"])

    def shutdown(self) -> None:
        """Signal all threads to stop and wait for cleanup."""
        self.shutdown_event.set()
        for t in self.processing_threads:
            t.join(timeout=3)
        logger.info("All vision threads stopped")

    def set_active_camera(self, camera_index: int) -> None:
        """Set the active camera for YOLO inference."""
        self.active_camera_index = camera_index

    def reload_all_zones(self) -> None:
        """Notify all engines to reload zone definitions."""
        for engine in self.engines.values():
            engine.reload_zones()
        logger.info("Zones reloaded across %d engine(s)", len(self.engines))

    # ── WebSocket Broadcasting ──

    async def broadcast_telemetry(self) -> None:
        """Periodically pushes telemetry + queued alerts to all connected WS clients."""
        while True:
            await asyncio.sleep(0.1)  # 10 Hz

            payload = {
                "active_targets": sum(e.telemetry["active_targets"] for e in self.engines.values()),
                "state": "BREACH" if any(
                    e.telemetry["state"] == "BREACH" for e in self.engines.values()
                ) else "SECURE",
                "cameras": [e.telemetry for e in self.engines.values()],
            }

            # Attach any pending breach alerts
            alerts = []
            for engine in self.engines.values():
                while engine.pending_events:
                    alerts.append(engine.pending_events.pop(0))

            if alerts:
                payload["alerts"] = alerts

            data = json.dumps(payload)

            # Broadcast to all connected clients
            stale: List[WebSocket] = []
            for ws in self.ws_clients:
                try:
                    await ws.send_text(data)
                except Exception:
                    stale.append(ws)

            for ws in stale:
                try:
                    self.ws_clients.remove(ws)
                except ValueError:
                    pass

    def add_ws_client(self, ws: WebSocket) -> None:
        """Register a new WebSocket client."""
        self.ws_clients.append(ws)

    def remove_ws_client(self, ws: WebSocket) -> None:
        """Unregister a WebSocket client."""
        try:
            self.ws_clients.remove(ws)
        except ValueError:
            pass

    # ── Internal ──

    def _open_camera(self, index: int):
        """Open camera by index; falls back to SyntheticVideoSource if unavailable."""
        try:
            cap = cv2.VideoCapture(index)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None and frame.size > 0:
                    logger.info("Camera %d opened and verified", index)
                    return cap
                else:
                    logger.warning("Camera %d opened but test frame failed — skipping", index)
            cap.release()
        except Exception as e:
            logger.error("Camera %d error: %s", index, e)

        logger.info("Camera %d unavailable — falling back to synthetic feed", index)
        return SyntheticVideoSource()

    def _vision_loop(self, camera_index: int, camera_name: str) -> None:
        """Runs in a daemon thread — reads and processes frames for a specific camera."""
        settings = get_settings()
        cap = self._open_camera(camera_index)
        self.video_captures[camera_index] = cap

        vision_engine = VirtualFenceEngine(camera_index, camera_name)
        vision_engine.reload_zones()
        self.engines[camera_index] = vision_engine

        failed_reads = 0
        frame_count = 0

        while not self.shutdown_event.is_set():
            ret, frame = cap.read()
            if not ret or frame is None or frame.size == 0:
                failed_reads += 1
                if failed_reads > 30:
                    logger.warning("Camera %d stalled — falling back to synthetic feed", camera_index)
                    cap.release()
                    cap = SyntheticVideoSource()
                    self.video_captures[camera_index] = cap
                    failed_reads = 0
                time.sleep(0.033)
                continue

            failed_reads = 0
            frame_count += 1

            # Performance optimization: skip frames
            if frame_count % settings.FRAME_SKIP != 0:
                continue

            # Skip heavy YOLO inference for background cameras
            if camera_index != self.active_camera_index:
                continue

            vision_engine.process_frame(frame)

        cap.release()
        logger.info("Vision loop stopped for camera %d", camera_index)


# Singleton instance
camera_manager = CameraManager()
