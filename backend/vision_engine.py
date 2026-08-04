"""
Virtual Fence — Computer Vision Engine (YOLOv8 + Multi-Camera)
"""

import json
import os
import threading
import time
import uuid
import collections
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
from ultralytics import YOLO

import logging
logging.getLogger("ultralytics").setLevel(logging.ERROR)

from backend.database import SessionLocal
from backend.models import ZoneModel, IncidentModel

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
FRAME_W, FRAME_H = 640, 480
BREACH_THRESHOLD = 5
BUFFER_SIZE = 150  # 5 seconds at 30 fps
SNAPSHOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "storage", "snapshots")
VIDEO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "storage", "videos")
os.makedirs(SNAPSHOT_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

# Removed TARGET_CLASSES filter to track all 80 COCO classes

# Path to YOLO model weights (upgraded to 'small' model for better detection accuracy)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_YOLO_WEIGHTS = os.path.join(_PROJECT_ROOT, "yolov8s.pt")
if not os.path.isfile(_YOLO_WEIGHTS):
    _YOLO_WEIGHTS = "yolov8s.pt"  # fallback: let ultralytics download

_COLORS = [
    (0, 255, 255),   # Yellow
    (255, 0, 255),   # Magenta
    (0, 255, 0),     # Green
    (255, 128, 0),   # Blue-ish
    (0, 128, 255),   # Orange
    (255, 0, 0),     # Blue
    (0, 0, 255),     # Red
    (255, 153, 204), # Pink
    (153, 255, 51),  # Lime
    (204, 153, 255), # Purple
]

def get_color(cls_id: int):
    return _COLORS[cls_id % len(_COLORS)]


class _TrackedTarget:
    __slots__ = ("id", "cx", "cy", "bbox", "cls", "breach_counters")

    def __init__(self, tid: int, cx: int, cy: int, bbox: Tuple[int, int, int, int], cls: int):
        self.id = tid
        self.cx = cx
        self.cy = cy
        self.bbox = bbox
        self.cls = cls
        self.breach_counters: Dict[str, int] = {}

class VirtualFenceEngine:
    def __init__(self, camera_index: int, camera_name: str) -> None:
        self.camera_index = camera_index
        self.camera_name = camera_name
        self._targets: Dict[int, _TrackedTarget] = {}
        self._zones: List[dict] = []
        self.latest_jpeg: Optional[bytes] = None
        self.pending_events: List[dict] = []
        self.telemetry: dict = {
            "active_targets": 0,
            "state": "SECURE",
            "targets": [],
            "camera_index": camera_index,
            "camera_name": camera_name,
        }
        
        # Each engine gets its own YOLO model so tracker state is isolated per camera
        self._model = YOLO(_YOLO_WEIGHTS)
        print(f"[Virtual Fence] YOLO model loaded for {camera_name} (camera {camera_index})")
        
        # Rolling buffer for video
        self._frame_buffer = collections.deque(maxlen=BUFFER_SIZE)
        self._recording = False
        self._recording_frames_left = 0
        self._recording_incident_id = None
        self._recording_zone = None
        self._recording_buffer = []

    def reload_zones(self) -> None:
        db = SessionLocal()
        try:
            rows = db.query(ZoneModel).filter(ZoneModel.is_active == True).all()
            loaded: List[dict] = []
            for z in rows:
                raw_points = json.loads(z.points)
                abs_pts = np.array(
                    [[int(p[0] * FRAME_W), int(p[1] * FRAME_H)] for p in raw_points],
                    dtype=np.int32,
                )
                loaded.append({"id": z.id, "name": z.name, "contour_pts": abs_pts})
            self._zones = loaded
        finally:
            db.close()

    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        frame = cv2.resize(frame, (FRAME_W, FRAME_H))
        annotated = frame.copy()
        
        # Save to rolling buffer (unannotated)
        self._frame_buffer.append(frame.copy())
        
        model = self._model
        
        # Run YOLO tracking (tracking all classes)
        results = model.track(frame, persist=True, conf=0.3, verbose=False)
        
        current_target_ids = set()
        target_list = []
        breach_active = False
        
        if len(results) > 0 and results[0].boxes is not None and results[0].boxes.id is not None:
            boxes = results[0].boxes.xywh.cpu().numpy()
            track_ids = results[0].boxes.id.cpu().numpy().astype(int)
            classes = results[0].boxes.cls.cpu().numpy().astype(int)
            
            for box, track_id, cls in zip(boxes, track_ids, classes):
                cx, cy, w, h = box
                cx, cy, w, h = int(cx), int(cy), int(w), int(h)
                x = int(cx - w / 2)
                y = int(cy - h / 2)
                
                if track_id not in self._targets:
                    self._targets[track_id] = _TrackedTarget(track_id, cx, cy, (x, y, w, h), cls)
                else:
                    t = self._targets[track_id]
                    t.cx = cx
                    t.cy = cy
                    t.bbox = (x, y, w, h)
                
                current_target_ids.add(track_id)
                t = self._targets[track_id]
                
                # Draw Box
                label_name = model.names.get(cls, f"CLS-{cls}")
                label_text = f"ID-{track_id} {label_name}"
                color = get_color(int(cls))
                
                # Rectangle for object
                cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 3)
                
                # Text Background
                (tw, th), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                cv2.rectangle(annotated, (x, max(0, y - th - 10)), (x + tw + 4, y), color, -1)
                
                # Text Label (Black text on colored background for visibility)
                cv2.putText(annotated, label_text, (x + 2, y - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
                
                target_list.append({"id": int(track_id), "cx": cx, "cy": cy, "bbox": [x, y, w, h], "label": label_name})
                
                # Check Zones
                for zone in self._zones:
                    inside = cv2.pointPolygonTest(zone["contour_pts"], (float(cx), float(cy)), False)
                    zid = zone["id"]
                    if inside >= 0:
                        t.breach_counters[zid] = t.breach_counters.get(zid, 0) + 1
                        if t.breach_counters[zid] == BREACH_THRESHOLD:
                            breach_active = True
                            self._trigger_breach(t, zone, annotated)
                        elif t.breach_counters[zid] > BREACH_THRESHOLD:
                            breach_active = True
                    else:
                        t.breach_counters[zid] = 0

        # Remove lost targets
        to_remove = [tid for tid in self._targets if tid not in current_target_ids]
        for tid in to_remove:
            del self._targets[tid]

        # Draw zones
        for zone in self._zones:
            cv2.polylines(annotated, [zone["contour_pts"]], True, (0, 0, 255), 2)
            if len(zone["contour_pts"]) > 0:
                label_pt = tuple(zone["contour_pts"][0])
                cv2.putText(annotated, zone["name"], (label_pt[0], label_pt[1] - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

        # HUD
        state_text = "!! BREACH DETECTED !!" if breach_active else "SECURE"
        state_color = (0, 0, 255) if breach_active else (0, 255, 0)
        cv2.putText(annotated, f"[{self.camera_name}] {state_text}", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, state_color, 2)
        
        self.telemetry = {
            "active_targets": len(self._targets),
            "state": "BREACH" if breach_active else "SECURE",
            "targets": target_list,
            "camera_index": self.camera_index,
            "camera_name": self.camera_name,
        }

        # Encode JPEG
        _, buf = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 75])
        self.latest_jpeg = buf.tobytes()

        # Handle recording state
        if self._recording:
            self._recording_buffer.append(frame.copy())
            self._recording_frames_left -= 1
            if self._recording_frames_left <= 0:
                self._recording = False
                # Save video asynchronously
                frames_to_save = list(self._recording_buffer)
                incident_id = self._recording_incident_id
                threading.Thread(target=self._save_video, args=(frames_to_save, incident_id)).start()

        return annotated

    def _trigger_breach(self, target: _TrackedTarget, zone: dict, annotated_frame: np.ndarray) -> None:
        incident_id = str(uuid.uuid4())
        filename = f"{incident_id}.jpg"
        filepath = os.path.join(SNAPSHOT_DIR, filename)

        # Save snapshot
        snap = annotated_frame.copy()
        cv2.putText(snap, f"BREACH — {zone['name']}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        cv2.imwrite(filepath, snap)

        # Start recording
        self._recording = True
        self._recording_frames_left = BUFFER_SIZE
        self._recording_incident_id = incident_id
        self._recording_zone = zone
        # copy past frames
        self._recording_buffer = list(self._frame_buffer)

        # Initial DB record
        now = datetime.now(timezone.utc)
        db = SessionLocal()
        try:
            record = IncidentModel(
                id=incident_id,
                zone_id=zone["id"],
                object_id=target.id,
                timestamp=now,
                snapshot_path=f"/snapshots/{filename}",
                video_path=None,
                status="UNREAD",
            )
            db.add(record)
            db.commit()
        finally:
            db.close()

        # Queue WebSocket event
        event = {
            "type": "BREACH_ALERT",
            "incident_id": incident_id,
            "zone_id": zone["id"],
            "zone_name": zone["name"],
            "object_id": target.id,
            "timestamp": now.isoformat(),
            "snapshot_url": f"/snapshots/{filename}",
            "video_url": None,
            "camera_index": self.camera_index,
        }
        self.pending_events.append(event)

    def _save_video(self, frames: List[np.ndarray], incident_id: str):
        video_filename = f"{incident_id}.mp4"
        video_path = os.path.join(VIDEO_DIR, video_filename)
        
        # Use mp4v codec
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(video_path, fourcc, 30.0, (FRAME_W, FRAME_H))
        for f in frames:
            out.write(f)
        out.release()
        
        # Update DB
        db = SessionLocal()
        try:
            incident = db.query(IncidentModel).filter(IncidentModel.id == incident_id).first()
            if incident:
                incident.video_path = f"/videos/{video_filename}"
                db.commit()
        finally:
            db.close()

class SyntheticVideoSource:
    def __init__(self) -> None:
        self._frame_idx = 0
        self._dot_x = 100.0
        self._dot_y = 240.0
        self._dx = 3.0
        self._dy = 2.0

    def read(self) -> Tuple[bool, np.ndarray]:
        frame = np.zeros((FRAME_H, FRAME_W, 3), dtype=np.uint8)
        for gx in range(0, FRAME_W, 40):
            cv2.line(frame, (gx, 0), (gx, FRAME_H), (25, 35, 25), 1)
        for gy in range(0, FRAME_H, 40):
            cv2.line(frame, (0, gy), (FRAME_W, gy), (25, 35, 25), 1)

        self._dot_x += self._dx
        self._dot_y += self._dy
        if self._dot_x < 30 or self._dot_x > FRAME_W - 60:
            self._dx *= -1
        if self._dot_y < 30 or self._dot_y > FRAME_H - 100:
            self._dy *= -1

        px, py = int(self._dot_x), int(self._dot_y)
        # Draw a synthetic "person"
        cv2.rectangle(frame, (px, py), (px + 30, py + 70), (180, 180, 180), -1)
        cv2.circle(frame, (px + 15, py - 10), 12, (180, 180, 180), -1)

        cv2.putText(frame, "SYNTHETIC FEED", (140, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 200, 200), 1)
        self._frame_idx += 1
        time.sleep(0.033)
        return True, frame

    def release(self) -> None:
        pass

    def isOpened(self) -> bool:
        return True
