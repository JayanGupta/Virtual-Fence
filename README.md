# Virtual Fence (Enterprise Spatial Boundary System)

[![CI](https://github.com/VirtualFenceTeam/virtual-fence/actions/workflows/ci.yml/badge.svg)](https://github.com/VirtualFenceTeam/virtual-fence/actions)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An enterprise-ready spatial perimeter security platform that processes real-time camera streams to monitor user-defined coordinate boundaries, track movement vectors, and instantly log security breaches.

![Virtual Fence Demo](demo.gif)

## Features

- **Real-time Object Detection**: YOLOv8-powered detection with sub-50ms inference.
- **Multi-Camera Orchestration**: Monitor multiple feeds simultaneously with independent thread processing.
- **Spatial Boundary Definitions**: Draw polygonal intrusion zones over camera feeds.
- **Automated Incident Recording**: Rolling buffer automatically saves 10-second MP4 clips of breaches.
- **RESTful API & WebSocket Telemetry**: Integration-ready endpoints for enterprise SOC dashboards.

---

## Architectural Overview

The platform uses a unified single-service architecture for ease of deployment, combining FastAPI, SQLite, and a Next.js Static Export.

```mermaid
graph TD
    Client[Next.js 14 SPA Dashboard] <-->|HTTP REST / WebSockets| Server[FastAPI Server]
    Server <-->|ORM| SQLite[(SQLite Database)]
    Server <-->|In-Memory Buffer| Engine[Virtual Fence Engine (YOLOv8)]
    Engine <-->|Read Frames| Camera[Camera / Synthetic Video Source]
```

## Quick Start (Local Development)

### Prerequisites
- Python 3.11+
- Node.js 20+

### Windows Startup
Run the automated batch script:
```cmd
start.bat
```
*This script verifies dependencies, creates a virtual environment, builds the Next.js frontend, and launches the unified FastAPI server.*

### Manual Startup (Linux/macOS)
```bash
# 1. Setup Backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Build Frontend
cd frontend
npm ci
npm run build
cd ..

# 3. Launch Server
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

---

## Deployment (Docker)

Virtual Fence is containerized for production deployment.

```bash
# Build the image
docker build -t virtual-fence:latest .

# Run the container
docker run -d \
  -p 8000:8000 \
  -v virtual_fence_data:/app/backend/storage \
  --name virtual-fence \
  virtual-fence:latest
```

*Note: For camera passthrough on Linux, you may need to map devices (e.g., `--device /dev/video0`).*

---

## Configuration

Configuration is managed via environment variables. Create a `.env` file in the root directory:

```env
LOG_LEVEL=INFO
CORS_ORIGINS=["http://localhost:8000"]
FRAME_WIDTH=640
FRAME_HEIGHT=480
BREACH_THRESHOLD=5
```
See `.env.example` for all configurable options.

---

## Documentation

Once the server is running, interactive API documentation is available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Contributing
Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to this project.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
