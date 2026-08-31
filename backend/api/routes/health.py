from fastapi import APIRouter

from api.schemas.detection import HealthResponse
from core.config import settings

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    model_loaded = settings.yolo_weights_path.exists()
    return HealthResponse(status="ok", model_loaded=model_loaded, app_env=settings.app_env)
