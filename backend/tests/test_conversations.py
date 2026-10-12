def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def test_create_conversation_and_send_message(client, user_token, second_user_token, db):
    token_a, user_a = user_token
    token_b, user_b = second_user_token

    resp = client.post("/api/conversations", json={"user_id": user_b}, headers=auth_header(token_a))
    assert resp.status_code == 201
    conversation_id = resp.get_json()["conversation_id"]

    send_resp = client.post(f"/api/conversations/{conversation_id}/messages",
                             json={"content": "hello there"}, headers=auth_header(token_a))
    assert send_resp.status_code == 201

    # Message is stored encrypted, never plaintext, in the DB.
    stored = db.messages.find_one({"conversation_id": conversation_id})
    assert "hello there" not in stored["ciphertext"]
    assert stored["ciphertext"] and stored["nonce"]

    # Recipient can read it back decrypted correctly.
    read_resp = client.get(f"/api/conversations/{conversation_id}/messages", headers=auth_header(token_b))
    assert read_resp.status_code == 200
    messages = read_resp.get_json()["messages"]
    assert messages[0]["content"] == "hello there"
    assert messages[0]["sender_id"] == user_a


def test_conversation_idempotent(client, user_token, second_user_token):
    token_a, user_a = user_token
    _, user_b = second_user_token
    r1 = client.post("/api/conversations", json={"user_id": user_b}, headers=auth_header(token_a))
    r2 = client.post("/api/conversations", json={"user_id": user_b}, headers=auth_header(token_a))
    assert r1.get_json()["conversation_id"] == r2.get_json()["conversation_id"]


def test_non_participant_cannot_read_messages(client, user_token, second_user_token, third_user_token):
    token_a, user_a = user_token
    token_b, user_b = second_user_token
    token_c, _ = third_user_token

    conv_resp = client.post("/api/conversations", json={"user_id": user_b}, headers=auth_header(token_a))
    conversation_id = conv_resp.get_json()["conversation_id"]
    client.post(f"/api/conversations/{conversation_id}/messages", json={"content": "secret"}, headers=auth_header(token_a))

    resp = client.get(f"/api/conversations/{conversation_id}/messages", headers=auth_header(token_c))
    assert resp.status_code == 403


def test_non_participant_cannot_send_messages(client, user_token, second_user_token, third_user_token):
    token_a, _ = user_token
    _, user_b = second_user_token
    token_c, _ = third_user_token

    conv_resp = client.post("/api/conversations", json={"user_id": user_b}, headers=auth_header(token_a))
    conversation_id = conv_resp.get_json()["conversation_id"]

    resp = client.post(f"/api/conversations/{conversation_id}/messages", json={"content": "intrusion"}, headers=auth_header(token_c))
    assert resp.status_code == 403


def test_cannot_message_nonexistent_conversation(client, user_token):
    token, _ = user_token
    resp = client.post("/api/conversations/does-not-exist/messages", json={"content": "hi"}, headers=auth_header(token))
    assert resp.status_code == 404
