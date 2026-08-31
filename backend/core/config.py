"""
Centralized application settings.

All configuration is loaded from environment variables (see .env.example).
Never hardcode paths, thresholds, or secrets elsewhere in the codebase —
import `settings` from this module instead.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    # Database
    database_url: str = "postgresql+psycopg2://naval_user:naval_pass@localhost:5432/naval_ai"

    # Background job queue (used for video processing — see core/queue.py, worker.py)
    redis_url: str = "redis://localhost:6379/0"

    # Auth
    jwt_secret_key: str = "change-me-in-production"  # override via .env — never ship this default
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24  # 24h

    # Storage
    upload_dir: Path = Path("./uploads")
    output_dir: Path = Path("./outputs")
    report_dir: Path = Path("./reports")

    # Model — standard (clear-weather) weights
    yolo_weights_path: Path = Path("../models/weights/best.pt")
    yolo_device: str = "cpu"
    yolo_conf_threshold: float = 0.35
    yolo_iou_threshold: float = 0.45

    # Model — all-weather weights (blur / fog / rain tolerant)
    # Lower conf threshold to catch ships in degraded images.
    all_weather_weights_path: Path = Path("../models/weights/all_weather_best.pt")
    all_weather_conf_threshold: float = 0.25

    # Video
    tracker_type: str = "bytetrack"
    max_video_duration_seconds: int = 300

    # CORS
    allowed_origins: str = "http://localhost:3000"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    def ensure_directories(self) -> None:
        for d in (self.upload_dir, self.output_dir, self.report_dir):
            d.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
