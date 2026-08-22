"""
Virtual Fence — FastAPI Application
App factory pattern: creates the app, mounts routers, configures middleware,
and manages the application lifecycle.
"""

import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from backend.config import get_settings
from backend.database import Base, engine
from backend.exceptions import VirtualFenceError, virtual_fence_error_handler, generic_exception_handler
from backend.logging_config import setup_logging, get_logger
from backend.middleware import RequestIDMiddleware, SecurityHeadersMiddleware, RequestTimingMiddleware
from backend.routers import zones, incidents, health
from backend.routers.cameras import router as cameras_router, ws_router as cameras_ws_router
from backend.services.camera_service import camera_manager

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_BACKEND_DIR)
_FRONTEND_OUT = os.path.join(_PROJECT_ROOT, "frontend", "out")

settings = get_settings()

# Initialize logging
setup_logging()
logger = get_logger("app")


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    # ── Startup ──
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ensured")

    # Enumerate cameras
    camera_manager.enumerate_cameras()

    # Start vision processing threads
    camera_manager.start_all()

    # Start WebSocket telemetry broadcaster
    broadcaster = asyncio.create_task(camera_manager.broadcast_telemetry())
    logger.info("System online — http://%s:%d", settings.HOST, settings.PORT)

    yield

    # ── Shutdown ──
    camera_manager.shutdown()
    broadcaster.cancel()
    logger.info("Shutdown complete")


# ---------------------------------------------------------------------------
# App Factory
# ---------------------------------------------------------------------------
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Exception Handlers ──
app.add_exception_handler(VirtualFenceError, virtual_fence_error_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# ── Middleware (order matters: outermost first) ──
app.add_middleware(RequestTimingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──
app.include_router(zones.router)
app.include_router(incidents.router)
app.include_router(cameras_router)
app.include_router(cameras_ws_router)
app.include_router(health.router)

# ── Static File Mounts ──
app.mount("/snapshots", StaticFiles(directory=settings.SNAPSHOTS_DIR), name="snapshots")
app.mount("/videos", StaticFiles(directory=settings.VIDEOS_DIR), name="videos")


# ---------------------------------------------------------------------------
# SPA Catch-All
# ---------------------------------------------------------------------------
if os.path.isdir(_FRONTEND_OUT):
    @app.api_route("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        """Serve the Next.js static export with client-side routing support."""
        # Skip API/WS/static paths
        reserved = ("api/", "ws/", "snapshots/", "videos/", "docs", "redoc", "openapi.json")
        if any(full_path.startswith(prefix) for prefix in reserved):
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Not Found")

        # Try exact file
        file_path = os.path.join(_FRONTEND_OUT, full_path)
        if os.path.isfile(file_path):
            from fastapi.responses import FileResponse
            return FileResponse(file_path)

        # Try .html extension
        html_file = os.path.join(_FRONTEND_OUT, f"{full_path}.html")
        if os.path.isfile(html_file):
            with open(html_file, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())

        # Try subdirectory index
        sub_index = os.path.join(_FRONTEND_OUT, full_path, "index.html")
        if os.path.isfile(sub_index):
            with open(sub_index, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())

        # SPA fallback
        fallback_path = os.path.join(_FRONTEND_OUT, "index.html")
        if os.path.isfile(fallback_path):
            with open(fallback_path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())

        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Page not found")

    app.mount("/", StaticFiles(directory=_FRONTEND_OUT, html=True), name="spa")
    logger.info("SPA static files mounted from %s", _FRONTEND_OUT)
else:
    @app.get("/")
    def _fallback_root():
        return HTMLResponse(
            "<html><body style='background:#0f172a;color:#e2e8f0;font-family:sans-serif;'>"
            "<div style='text-align:center'><h1>Virtual Fence API</h1>"
            "<p>Frontend not built. Visit <a href='/docs' style='color:#facc15'>/docs</a> for API documentation.</p>"
            "</div></body></html>"
        )
