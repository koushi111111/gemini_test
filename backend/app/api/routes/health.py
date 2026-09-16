"""ヘルスチェック。docker-compose / Cloud Run の死活監視に使う。"""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.schemas.chat import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health(settings: Annotated[Settings, Depends(get_settings)]) -> HealthResponse:
    return HealthResponse(
        app=settings.app_name,
        environment=settings.environment,
        version="0.1.0",
    )
