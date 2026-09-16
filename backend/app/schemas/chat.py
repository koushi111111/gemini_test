"""チャット API のリクエスト / レスポンススキーマ。"""

from typing import Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "model"] = Field(..., description="発話者")
    content: str = Field(..., min_length=1, description="発話内容")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000, description="ユーザーの入力")
    history: list[ChatMessage] = Field(default_factory=list, description="直近の会話履歴(古い順)")


class ChatResponse(BaseModel):
    reply: str = Field(..., description="Gemini からの応答テキスト")
    model: str = Field(..., description="使用したモデル名")


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    app: str
    environment: str
    version: str
