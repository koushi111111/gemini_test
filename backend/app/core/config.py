"""アプリケーション設定。環境変数 / .env から読み込む。"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- アプリ基本設定 ---
    app_name: str = "tx_hackathon_gc-backend"
    environment: Literal["local", "dev", "prod"] = "local"
    log_level: str = "INFO"

    # CORS: Flutter Web の開発サーバなど
    cors_origins: list[str] = [
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:3000",
    ]

    # --- Google Cloud / Gemini 設定 ---
    # Vertex AI (Google Cloud) 経由で Gemini を呼ぶ場合は True
    google_genai_use_vertexai: bool = True
    google_cloud_project: str = ""
    google_cloud_location: str = "us-central1"
    # Vertex AI を使わない場合(AI Studio の API キー利用時)のみ設定
    google_api_key: str = ""

    gemini_model: str = "gemini-2.5-flash"
    gemini_temperature: float = 0.7
    gemini_max_output_tokens: int = 2048
    gemini_system_instruction: str = "あなたは日本語で簡潔かつ正確に回答するアシスタントです。"

    @property
    def is_local(self) -> bool:
        return self.environment == "local"


@lru_cache
def get_settings() -> Settings:
    """設定のシングルトン。DI (Depends) からも利用する。"""
    return Settings()
