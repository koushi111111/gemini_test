import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.schemas.chat import ChatMessage
from app.services.gemini import GeminiService, get_gemini_service


class FakeGeminiService(GeminiService):
    """外部 API を叩かないテスト用スタブ。"""

    async def generate_reply(self, message: str, history: list[ChatMessage]) -> str:
        return f"echo: {message}"


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_gemini_service] = FakeGeminiService
    return TestClient(app)
