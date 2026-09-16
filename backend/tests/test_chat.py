from fastapi.testclient import TestClient


def test_chat_returns_reply(client: TestClient) -> None:
    res = client.post("/api/v1/chat", json={"message": "こんにちは", "history": []})
    assert res.status_code == 200
    body = res.json()
    assert body["reply"] == "echo: こんにちは"
    assert body["model"]


def test_chat_rejects_empty_message(client: TestClient) -> None:
    res = client.post("/api/v1/chat", json={"message": "", "history": []})
    assert res.status_code == 422
