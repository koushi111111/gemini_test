"""Gemini (Google Cloud Vertex AI) クライアントのラッパー。

google-genai SDK を使い、Vertex AI 経由 / AI Studio 経由の両方に対応する。
どちらを使うかは設定 `google_genai_use_vertexai` で切り替える。
"""

import logging
from functools import lru_cache

from google import genai
from google.genai import types

from app.core.config import Settings, get_settings
from app.schemas.chat import ChatMessage

logger = logging.getLogger(__name__)


class GeminiError(RuntimeError):
    """Gemini 呼び出しに失敗したときの例外。"""


@lru_cache
def get_client() -> genai.Client:
    """genai.Client を生成して使い回す(接続確立コストを抑えるため)。"""
    settings = get_settings()

    if settings.google_genai_use_vertexai:
        if not settings.google_cloud_project:
            raise GeminiError("GOOGLE_CLOUD_PROJECT が未設定です。.env を確認してください。")
        return genai.Client(
            vertexai=True,
            project=settings.google_cloud_project,
            location=settings.google_cloud_location,
        )

    if not settings.google_api_key:
        raise GeminiError("GOOGLE_API_KEY が未設定です。.env を確認してください。")
    return genai.Client(api_key=settings.google_api_key)


def _to_contents(message: str, history: list[ChatMessage]) -> list[types.Content]:
    contents = [
        types.Content(role=m.role, parts=[types.Part.from_text(text=m.content)]) for m in history
    ]
    contents.append(types.Content(role="user", parts=[types.Part.from_text(text=message)]))
    return contents


class GeminiService:
    """チャット生成のユースケースを担うサービス層。"""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    async def generate_reply(self, message: str, history: list[ChatMessage]) -> str:
        settings = self._settings
        client = get_client()
        config = types.GenerateContentConfig(
            temperature=settings.gemini_temperature,
            max_output_tokens=settings.gemini_max_output_tokens,
            system_instruction=settings.gemini_system_instruction,
        )

        try:
            response = await client.aio.models.generate_content(
                model=settings.gemini_model,
                contents=_to_contents(message, history),
                config=config,
            )
        except Exception as exc:  # SDK 例外はまとめて業務例外に変換する
            logger.exception("Gemini の呼び出しに失敗しました")
            raise GeminiError(str(exc)) from exc

        text = response.text
        if not text:
            raise GeminiError("Gemini から空の応答が返りました")
        return text


def get_gemini_service() -> GeminiService:
    """FastAPI の Depends 用ファクトリ。テスト時は override して差し替える。"""
    return GeminiService()
