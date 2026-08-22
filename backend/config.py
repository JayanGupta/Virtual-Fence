"""
Virtual Fence — Centralized Configuration
Uses Pydantic Settings for type-safe configuration with environment variable overrides.
"""

import os
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings with environment variable overrides."""

    # ── Application ──
    APP_NAME: str = "Virtual Fence"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "Enterprise Autonomous Perimeter Intrusion & Spatial Boundary System"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # ── Server ──
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ── Database ──
    DATABASE_URL: str = Field(
        default="",
        description="SQLAlchemy database URL. Auto-generated if empty.",
    )

    # ── CORS ──
    CORS_ORIGINS: List[str] = ["*"]

    # ── Vision Engine ──
    FRAME_WIDTH: int = 640
    FRAME_HEIGHT: int = 480
    BREACH_THRESHOLD: int = 5
    FRAME_BUFFER_SIZE: int = 150  # ~5 seconds at 30 fps
    YOLO_MODEL: str = "yolov8s.pt"
    YOLO_CONFIDENCE: float = 0.3
    YOLO_TRACKER: str = "bytetrack.yaml"
    JPEG_QUALITY: int = 75
    MAX_CAMERA_SCAN: int = 6
    FRAME_SKIP: int = 3  # Process 1 in every N frames

    # ── Incident Management ──
    MAX_INCIDENTS_RETURNED: int = 100
    MAX_INCIDENT_BUFFER: int = 200

    # ── Rate Limiting ──
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # ── Paths ──
    STORAGE_DIR: str = ""
    SNAPSHOTS_DIR: str = ""
    VIDEOS_DIR: str = ""

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
    }

    def model_post_init(self, __context) -> None:
        """Resolve default paths after initialization."""
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(backend_dir)

        if not self.STORAGE_DIR:
            self.STORAGE_DIR = os.path.join(backend_dir, "storage")

        if not self.SNAPSHOTS_DIR:
            self.SNAPSHOTS_DIR = os.path.join(self.STORAGE_DIR, "snapshots")

        if not self.VIDEOS_DIR:
            self.VIDEOS_DIR = os.path.join(self.STORAGE_DIR, "videos")

        if not self.DATABASE_URL:
            self.DATABASE_URL = f"sqlite:///{os.path.join(self.STORAGE_DIR, 'virtual_fence.db')}"

        # Resolve YOLO weights path
        yolo_path = os.path.join(project_root, self.YOLO_MODEL)
        if os.path.isfile(yolo_path):
            self.YOLO_MODEL = yolo_path

        # Ensure directories exist
        os.makedirs(self.SNAPSHOTS_DIR, exist_ok=True)
        os.makedirs(self.VIDEOS_DIR, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    """Cached singleton settings instance."""
    return Settings()
