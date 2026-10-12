def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def test_login_success(client, user_token, db):
    resp = client.post("/api/auth/login", json={"username": "reguser", "password": "Password123!"})
    assert resp.status_code == 200
    assert "token" in resp.get_json()


def test_login_wrong_password_generic_error(client, user_token):
    resp = client.post("/api/auth/login", json={"username": "reguser", "password": "wrong"})
    assert resp.status_code == 401
    assert resp.get_json()["error"] == "Invalid username or password."


def test_login_nonexistent_user_same_generic_error(client):
    resp = client.post("/api/auth/login", json={"username": "ghost", "password": "whatever"})
    assert resp.status_code == 401
    assert resp.get_json()["error"] == "Invalid username or password."


def test_me_requires_auth(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_me_returns_current_user(client, user_token):
    token, user_id = user_token
    resp = client.get("/api/auth/me", headers=auth_header(token))
    assert resp.status_code == 200
    assert resp.get_json()["id"] == user_id


def test_change_password_invalidates_old_token(client, user_token):
    token, _ = user_token
    resp = client.post("/api/auth/change-password",
                        json={"current_password": "Password123!", "new_password": "NewPassword456!"},
                        headers=auth_header(token))
    assert resp.status_code == 200

    old_token_resp = client.get("/api/auth/me", headers=auth_header(token))
    assert old_token_resp.status_code == 401

    new_token = resp.get_json()["token"]
    new_token_resp = client.get("/api/auth/me", headers=auth_header(new_token))
    assert new_token_resp.status_code == 200


def test_logout_invalidates_token(client, user_token):
    token, _ = user_token
    logout_resp = client.post("/api/auth/logout", headers=auth_header(token))
    assert logout_resp.status_code == 200

    resp = client.get("/api/auth/me", headers=auth_header(token))
    assert resp.status_code == 401


def test_weak_new_password_rejected(client, user_token):
    token, _ = user_token
    resp = client.post("/api/auth/change-password",
                        json={"current_password": "Password123!", "new_password": "weak"},
                        headers=auth_header(token))
    assert resp.status_code == 400
