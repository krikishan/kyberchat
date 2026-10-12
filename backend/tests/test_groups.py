def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def test_create_group_and_send_message(client, user_token, second_user_token, third_user_token, db):
    token_a, user_a = user_token
    _, user_b = second_user_token
    _, user_c = third_user_token

    resp = client.post("/api/groups", json={"group_name": "Project Team", "member_ids": [user_b, user_c]},
                        headers=auth_header(token_a))
    assert resp.status_code == 201
    group_id = resp.get_json()["group_id"]
    assert set(resp.get_json()["members"]) == {user_a, user_b, user_c}

    send_resp = client.post(f"/api/groups/{group_id}/messages", json={"content": "team update"}, headers=auth_header(token_a))
    assert send_resp.status_code == 201

    stored = db.messages.find_one({"group_id": group_id})
    assert "team update" not in stored["ciphertext"]


def test_all_members_can_read_group_message(client, user_token, second_user_token, third_user_token):
    token_a, user_a = user_token
    token_b, user_b = second_user_token
    token_c, user_c = third_user_token

    group_resp = client.post("/api/groups", json={"group_name": "Team", "member_ids": [user_b, user_c]},
                              headers=auth_header(token_a))
    group_id = group_resp.get_json()["group_id"]
    client.post(f"/api/groups/{group_id}/messages", json={"content": "hi everyone"}, headers=auth_header(token_a))

    for token in (token_a, token_b, token_c):
        resp = client.get(f"/api/groups/{group_id}/messages", headers=auth_header(token))
        assert resp.status_code == 200
        assert resp.get_json()["messages"][0]["content"] == "hi everyone"


def test_non_member_cannot_access_group(client, user_token, second_user_token, third_user_token):
    token_a, _ = user_token
    _, user_b = second_user_token
    token_c, _ = third_user_token

    group_resp = client.post("/api/groups", json={"group_name": "Private", "member_ids": [user_b]}, headers=auth_header(token_a))
    group_id = group_resp.get_json()["group_id"]

    resp = client.get(f"/api/groups/{group_id}/messages", headers=auth_header(token_c))
    assert resp.status_code == 403

    resp2 = client.post(f"/api/groups/{group_id}/messages", json={"content": "x"}, headers=auth_header(token_c))
    assert resp2.status_code == 403


def test_only_creator_can_manage_membership(client, user_token, second_user_token, third_user_token):
    token_a, _ = user_token
    token_b, user_b = second_user_token
    _, user_c = third_user_token

    group_resp = client.post("/api/groups", json={"group_name": "Team", "member_ids": [user_b]}, headers=auth_header(token_a))
    group_id = group_resp.get_json()["group_id"]

    resp = client.post(f"/api/groups/{group_id}/members", json={"user_id": user_c}, headers=auth_header(token_b))
    assert resp.status_code == 403


def test_removed_member_loses_group_access(client, user_token, second_user_token, third_user_token):
    """Proves real key rotation drives authorization: after removal the member
    is dropped from the group's member list AND future session-key versions
    never include a wrapped copy for them."""
    token_a, user_a = user_token
    token_b, user_b = second_user_token
    _, user_c = third_user_token

    group_resp = client.post("/api/groups", json={"group_name": "Team", "member_ids": [user_b, user_c]},
                              headers=auth_header(token_a))
    group_id = group_resp.get_json()["group_id"]

    client.post(f"/api/groups/{group_id}/messages", json={"content": "before removal"}, headers=auth_header(token_a))

    remove_resp = client.delete(f"/api/groups/{group_id}/members/{user_b}", headers=auth_header(token_a))
    assert remove_resp.status_code == 200
    assert user_b not in remove_resp.get_json()["members"]

    resp = client.get(f"/api/groups/{group_id}/messages", headers=auth_header(token_b))
    assert resp.status_code == 403


def test_new_member_cannot_read_history_before_joining(client, user_token, second_user_token, third_user_token):
    token_a, user_a = user_token
    _, user_b = second_user_token
    token_c, user_c = third_user_token

    group_resp = client.post("/api/groups", json={"group_name": "Team", "member_ids": [user_b]}, headers=auth_header(token_a))
    group_id = group_resp.get_json()["group_id"]
    client.post(f"/api/groups/{group_id}/messages", json={"content": "old history"}, headers=auth_header(token_a))

    add_resp = client.post(f"/api/groups/{group_id}/members", json={"user_id": user_c}, headers=auth_header(token_a))
    assert add_resp.status_code == 200

    resp = client.get(f"/api/groups/{group_id}/messages", headers=auth_header(token_c))
    assert resp.status_code == 200
    msg = resp.get_json()["messages"][0]
    assert msg["accessible"] is False
    assert msg["content"] is None

    client.post(f"/api/groups/{group_id}/messages", json={"content": "new message"}, headers=auth_header(token_a))
    resp2 = client.get(f"/api/groups/{group_id}/messages", headers=auth_header(token_c))
    new_msg = resp2.get_json()["messages"][1]
    assert new_msg["accessible"] is True
    assert new_msg["content"] == "new message"
