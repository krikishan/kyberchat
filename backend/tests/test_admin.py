def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def test_admin_can_add_member(client, admin_token, db):
    token, _ = admin_token
    resp = client.post("/api/admin/users", json={"name": "Alice Doe", "email": "alice@example.com"},
                        headers=auth_header(token))
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["user"]["email"] == "alice@example.com"
    assert body["user"]["username"]

    stored = db.users.find_one({"email": "alice@example.com"})
    assert stored["must_change_password"] is True
    assert stored["password_hash"] != ""  # hashed, never plaintext
    assert "temp_password" not in body["user"]  # never returned to caller


def test_duplicate_email_rejected(client, admin_token):
    token, _ = admin_token
    client.post("/api/admin/users", json={"name": "Bob", "email": "bob@example.com"}, headers=auth_header(token))
    resp = client.post("/api/admin/users", json={"name": "Bob2", "email": "bob@example.com"}, headers=auth_header(token))
    assert resp.status_code == 400
    assert resp.get_json()["code"] == "duplicate_email"


def test_invalid_email_rejected(client, admin_token):
    token, _ = admin_token
    resp = client.post("/api/admin/users", json={"name": "X", "email": "not-an-email"}, headers=auth_header(token))
    assert resp.status_code == 400
    assert resp.get_json()["code"] == "invalid_email"


def test_regular_user_cannot_add_members(client, user_token):
    token, _ = user_token
    resp = client.post("/api/admin/users", json={"name": "Eve", "email": "eve@example.com"}, headers=auth_header(token))
    assert resp.status_code == 403


def test_unauthenticated_request_rejected(client):
    resp = client.post("/api/admin/users", json={"name": "Eve", "email": "eve@example.com"})
    assert resp.status_code == 401


def test_bulk_preview_deduplicates_and_validates(client, admin_token, db):
    token, _ = admin_token
    # pre-existing user
    client.post("/api/admin/users", json={"name": "Existing", "email": "existing@example.com"},
                headers=auth_header(token))

    raw_text = "new1@example.com, new1@example.com; not-an-email existing@example.com new2@example.com"
    resp = client.post("/api/admin/users/bulk/preview", json={"raw_text": raw_text}, headers=auth_header(token))
    assert resp.status_code == 200
    body = resp.get_json()
    assert "new1@example.com" in body["valid"]
    assert "new2@example.com" in body["valid"]
    assert "existing@example.com" in body["already_exists"]
    assert "new1@example.com" in body["duplicates_in_batch"]
    assert body["will_create"] == 2


def test_bulk_confirm_creates_only_confirmed_list(client, admin_token, db):
    token, _ = admin_token
    resp = client.post(
        "/api/admin/users/bulk/confirm",
        json={"emails": ["batch1@example.com", "batch2@example.com"]},
        headers=auth_header(token),
    )
    assert resp.status_code == 201
    body = resp.get_json()
    assert len(body["created"]) == 2
    assert db.users.count_documents({"email": {"$in": ["batch1@example.com", "batch2@example.com"]}}) == 2


def test_bulk_batch_size_limit_enforced(client, admin_token, app):
    token, _ = admin_token
    max_batch = app.config["BULK_ADD_MAX_BATCH"]
    emails = [f"user{i}@example.com" for i in range(max_batch + 1)]
    resp = client.post("/api/admin/users/bulk/confirm", json={"emails": emails}, headers=auth_header(token))
    assert resp.status_code == 400


def test_admin_can_deactivate_member(client, admin_token, db):
    token, _ = admin_token
    create_resp = client.post("/api/admin/users", json={"name": "Carl", "email": "carl@example.com"},
                               headers=auth_header(token))
    user_id = create_resp.get_json()["user"]["id"]

    resp = client.patch(f"/api/admin/users/{user_id}", json={"status": "inactive"}, headers=auth_header(token))
    assert resp.status_code == 200

    deactivated_user_login = client.post("/api/auth/login", json={"username": "carl@example.com", "password": "irrelevant"})
    assert deactivated_user_login.status_code == 401
