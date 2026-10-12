def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def test_team_members_excludes_self_and_sensitive_fields(client, user_token, second_user_token):
    token_a, user_a = user_token
    _, user_b = second_user_token

    resp = client.get("/api/team/members", headers=auth_header(token_a))
    assert resp.status_code == 200
    members = resp.get_json()["members"]
    ids = [m["id"] for m in members]
    assert user_a not in ids
    assert user_b in ids
    assert "email" not in members[0]
    assert "password_hash" not in members[0]


def test_team_members_requires_auth(client):
    resp = client.get("/api/team/members")
    assert resp.status_code == 401
