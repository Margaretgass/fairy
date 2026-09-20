from fastapi.testclient import TestClient

from fairy import web_app

client = TestClient(web_app.app)

DESKTOP_TOKEN = "desktop-session-token-with-enough-entropy"


def test_health_identifies_local_service():
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"service": "neurofairy", "status": "ok"}


def test_owned_backend_rejects_missing_or_wrong_desktop_token():
    protected = TestClient(web_app.create_app(api_token=DESKTOP_TOKEN))

    assert protected.get("/api/health").status_code == 401
    assert (
        protected.get(
            "/api/health",
            headers={"X-Fairy-Token": "wrong-token"},
        ).status_code
        == 401
    )


def test_owned_backend_accepts_matching_desktop_token():
    protected = TestClient(web_app.create_app(api_token=DESKTOP_TOKEN))

    response = protected.get(
        "/api/health",
        headers={"X-Fairy-Token": DESKTOP_TOKEN},
    )

    assert response.status_code == 200
    assert response.json() == {"service": "neurofairy", "status": "ok"}


def test_owned_backend_chat_requires_matching_token(monkeypatch):
    monkeypatch.setattr(web_app, "reply_to_user", lambda _message: "Open the document.")
    protected = TestClient(web_app.create_app(api_token=DESKTOP_TOKEN))

    rejected = protected.post("/api/chat", json={"message": "Help me start"})
    accepted = protected.post(
        "/api/chat",
        json={"message": "Help me start"},
        headers={"X-Fairy-Token": DESKTOP_TOKEN},
    )

    assert rejected.status_code == 401
    assert accepted.status_code == 200
    assert accepted.json() == {"reply": "Open the document."}


def test_chat_returns_trimmed_message_to_service(monkeypatch):
    messages: list[str] = []

    def fake_reply(message: str) -> str:
        messages.append(message)
        return "Open the document."

    monkeypatch.setattr(web_app, "reply_to_user", fake_reply)
    response = client.post("/api/chat", json={"message": "  I am stuck  "})

    assert response.status_code == 200
    assert response.json() == {"reply": "Open the document."}
    assert messages == ["I am stuck"]


def test_empty_chat_returns_local_prompt_without_calling_model(monkeypatch):
    def unexpected_call(message: str) -> str:
        raise AssertionError(f"model should not receive {message!r}")

    monkeypatch.setattr(web_app, "reply_to_user", unexpected_call)
    response = client.post("/api/chat", json={"message": "   "})

    assert response.status_code == 200
    assert response.json() == {"reply": "I’m here. Whenever you’re ready."}


def test_missing_message_is_rejected():
    response = client.post("/api/chat", json={})

    assert response.status_code == 422


def test_model_failure_returns_safe_fallback(monkeypatch):
    def failing_reply(message: str) -> str:
        raise RuntimeError(f"Ollama unavailable for {message!r}")

    monkeypatch.setattr(web_app, "reply_to_user", failing_reply)
    response = client.post("/api/chat", json={"message": "Help me start"})

    assert response.status_code == 200
    assert response.json()["reply"].startswith("I'm having trouble")


def test_root_serves_browser_ui():
    response = client.get("/")

    assert response.status_code == 200
    assert "ADHD Fairy" in response.text
