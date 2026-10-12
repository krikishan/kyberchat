def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def test_simulation_runs_real_crypto_and_succeeds(client, user_token):
    token, _ = user_token
    resp = client.post("/api/crypto/simulation", json={"message": "hello world"}, headers=auth_header(token))
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    assert body["recovered_message"] == "hello world"
    stage_names = [s["stage"] for s in body["stages"]]
    assert "ML-KEM Key Generation (Receiver)" in stage_names
    assert "AES-256-GCM Encryption" in stage_names


def test_simulation_never_exposes_secrets(client, user_token):
    token, _ = user_token
    resp = client.post("/api/crypto/simulation", json={"message": "sensitive"}, headers=auth_header(token))
    body = resp.get_json()
    dumped = str(body)
    # Only a hex preview of ciphertext is allowed — never raw session key material fields.
    for forbidden in ("secret_key", "private_key", "session_key", "shared_secret"):
        assert forbidden not in dumped


def test_crypto_self_test_passes(client, user_token):
    token, _ = user_token
    resp = client.post("/api/crypto/test", headers=auth_header(token))
    assert resp.status_code == 200
    assert resp.get_json()["passed"] is True


def test_performance_not_measured_before_any_run(client, user_token):
    token, _ = user_token
    resp = client.get("/api/performance", headers=auth_header(token))
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "Not measured"}


def test_only_admin_can_run_benchmark(client, user_token, admin_token):
    user_tok, _ = user_token
    resp = client.post("/api/performance/run", json={"trials": 3}, headers=auth_header(user_tok))
    assert resp.status_code == 403

    admin_tok, _ = admin_token
    admin_resp = client.post("/api/performance/run", json={"trials": 3}, headers=auth_header(admin_tok))
    assert admin_resp.status_code == 200
    assert admin_resp.get_json()["records_stored"] > 0


def test_performance_summary_reflects_real_measurements(client, admin_token, user_token):
    admin_tok, _ = admin_token
    client.post("/api/performance/run", json={"trials": 5}, headers=auth_header(admin_tok))

    user_tok, _ = user_token
    resp = client.get("/api/performance", headers=auth_header(user_tok))
    body = resp.get_json()
    assert "ML-KEM-768 / key_generation" in body
    assert body["ML-KEM-768 / key_generation"]["trials"] == 5
    assert body["ML-KEM-768 / key_generation"]["avg_ms"] > 0


def test_only_admin_can_export_csv(client, admin_token, user_token):
    admin_tok, _ = admin_token
    client.post("/api/performance/run", json={"trials": 2}, headers=auth_header(admin_tok))

    user_tok, _ = user_token
    resp = client.get("/api/performance/export", headers=auth_header(user_tok))
    assert resp.status_code == 403

    admin_resp = client.get("/api/performance/export", headers=auth_header(admin_tok))
    assert admin_resp.status_code == 200
    assert b"algorithm,operation" in admin_resp.data
