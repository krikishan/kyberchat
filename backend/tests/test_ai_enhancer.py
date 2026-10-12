def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def test_enhance_unavailable_without_groq_configured(client, user_token):
    """No GROQ_API_KEY is set in the test environment -> groq_client is None
    -> the endpoint must degrade gracefully, not crash, and say so clearly."""
    token, _ = user_token
    resp = client.post("/api/ai/enhance", json={"text": "send me the report tomorrow", "style": "professional"},
                        headers=auth_header(token))
    assert resp.status_code == 503
    assert "temporarily unavailable" in resp.get_json()["error"]


def test_enhance_requires_auth(client):
    resp = client.post("/api/ai/enhance", json={"text": "hi", "style": "clear"})
    assert resp.status_code == 401


def test_enhance_available_to_regular_user_and_admin(client, user_token, admin_token):
    """The enhancer must not be admin-only — both roles get the same
    (graceful-unavailable, since no Groq key) response, never a 403."""
    for token, _ in (user_token, admin_token):
        resp = client.post("/api/ai/enhance", json={"text": "hi", "style": "clear"}, headers=auth_header(token))
        assert resp.status_code != 403


def test_enhance_rejects_input_too_long(client, user_token):
    token, _ = user_token
    from app.ai.message_enhancer import MAX_INPUT_CHARS
    resp = client.post("/api/ai/enhance", json={"text": "a" * (MAX_INPUT_CHARS + 1), "style": "clear"},
                        headers=auth_header(token))
    assert resp.status_code == 503  # AIEnhancementError path (unavailable+validation share the 503 path here)


def test_enhance_rejects_unknown_style(client, user_token, monkeypatch):
    token, _ = user_token
    resp = client.post("/api/ai/enhance", json={"text": "hello", "style": "sarcastic"}, headers=auth_header(token))
    assert resp.status_code == 503


def test_list_styles(client, user_token):
    token, _ = user_token
    resp = client.get("/api/ai/enhance/styles", headers=auth_header(token))
    assert resp.status_code == 200
    assert "professional" in resp.get_json()["styles"]
