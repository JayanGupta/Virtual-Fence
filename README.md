# Virtual Fence (Enterprise Spatial Boundary System)

An enterprise-ready spatial perimeter security platform that processes real-time camera streams to monitor user-defined coordinate boundaries, track movement vectors, and instantly log security breaches.

![Virtual Fence Demo](demo.gif)

## Architectural Overview

The entire platform runs as a single-process architecture, delivering high performance and simple deployment.

```mermaid
graph TD
    Client[Next.js 14 SPA Dashboard] <-->|HTTP REST / WebSockets| Server[FastAPI Server]
    Server <-->|ORM| SQLite[(SQLite Database)]
    Server <-->|In-Memory Buffer| Engine[Virtual Fence Engine (YOLOv8)]
    Engine <-->|Read Frames| Camera[Camera / Synthetic Video Source]
```

### 1. The Computer Vision Pipeline (`backend/vision_engine.py`)
This engine utilizes a state-of-the-art **YOLOv8** model to detect, classify, and track objects in real-time.

* **Object Detection**: Powered by **YOLOv8** (`ultralytics`). It dynamically detects and classifies objects, specifically filtering for humans and vehicles to eliminate false positives.
* **Multi-Camera Processing**: The backend seamlessly spins up a dedicated background thread and YOLO vision engine instance for *every* camera detected on the system simultaneously.
* **Vector Tracking**: Associates targets across successive frames using YOLO's built-in tracker.
* **Intrusion Testing**: Normalized custom polygonal vertices drawn on the UI are denormalized to absolute resolution coordinates. Target centroids are evaluated against these coordinates using a ray-casting **Point-in-Polygon test** (`cv2.pointPolygonTest`).
* **Video Clip Recording**: When a breach is detected, the engine flags a 150-frame (5-second) rolling buffer, continues recording for an additional 5 seconds, and then encodes a 10-second `MP4` video clip of the entire incident using `cv2.VideoWriter`.

### 2. Backend Server (`backend/main.py`)
- **FastAPI**: Manages async non-blocking execution. Runs the OpenCV video loops in daemon threads.
- **WebSocket Telemetry**: Telemetry payloads detailing coordinate states and target counts are broadcast at 10Hz to all active console connections.
- **SPA Mounting**: In production, FastAPI mounts static SPA assets compiled from Next.js, serving client-side routing catchalls, snapshots, videos, and REST APIs from `http://localhost:8000`.

### 3. Frontend Web Console (`frontend/`)
- Built with **Next.js 14 (App Router)** and **TypeScript**, configured with static export output.
- Features a **Responsive Multi-Camera Grid Layout** allowing users to monitor all live camera feeds simultaneously.
- Incident Drawer embeds an HTML5 `<video>` player to review 10-second incident recordings instantly.

---

## Local Development Startup

Simply run the batch script in the root directory:
```cmd
start.bat
```
*This script will verify your Python and Node.js versions, create an isolated virtual environment (`venv`), install requirements, compile the frontend static files, and launch the server automatically.*
