import io


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def test_upload_and_download_roundtrip_in_conversation(client, user_token, second_user_token, db):
    token_a, user_a = user_token
    token_b, user_b = second_user_token

    conv_resp = client.post("/api/conversations", json={"user_id": user_b}, headers=auth_header(token_a))
    conversation_id = conv_resp.get_json()["conversation_id"]

    content = b"%PDF-1.4 fake pdf content for testing"
    data = {
        "file": (io.BytesIO(content), "report.pdf"),
        "context_type": "conversation",
        "context_id": conversation_id,
    }
    upload_resp = client.post("/api/files", data=data, headers=auth_header(token_a), content_type="multipart/form-data")
    assert upload_resp.status_code == 201
    file_id = upload_resp.get_json()["file_id"]

    stored = db.files.find_one({"file_id": file_id})
    assert content not in bytes(stored["ciphertext"])  # stored encrypted, not plaintext

    download_resp = client.get(f"/api/files/{file_id}/download", headers=auth_header(token_b))
    assert download_resp.status_code == 200
    assert download_resp.data == content


def test_non_participant_cannot_download(client, user_token, second_user_token, third_user_token):
    token_a, _ = user_token
    _, user_b = second_user_token
    token_c, _ = third_user_token

    conv_resp = client.post("/api/conversations", json={"user_id": user_b}, headers=auth_header(token_a))
    conversation_id = conv_resp.get_json()["conversation_id"]

    data = {"file": (io.BytesIO(b"secret contents"), "notes.txt"),
            "context_type": "conversation", "context_id": conversation_id}
    upload_resp = client.post("/api/files", data=data, headers=auth_header(token_a), content_type="multipart/form-data")
    file_id = upload_resp.get_json()["file_id"]

    resp = client.get(f"/api/files/{file_id}/download", headers=auth_header(token_c))
    assert resp.status_code == 403


def test_disallowed_file_type_rejected(client, user_token, second_user_token):
    token_a, _ = user_token
    _, user_b = second_user_token
    conv_resp = client.post("/api/conversations", json={"user_id": user_b}, headers=auth_header(token_a))
    conversation_id = conv_resp.get_json()["conversation_id"]

    data = {"file": (io.BytesIO(b"#!/bin/sh\necho pwned"), "malware.sh"),
            "context_type": "conversation", "context_id": conversation_id}
    resp = client.post("/api/files", data=data, headers=auth_header(token_a), content_type="multipart/form-data")
    assert resp.status_code == 400
    assert resp.get_json()["code"] == "invalid_type"


def test_path_traversal_filename_rejected(client, user_token, second_user_token):
    token_a, _ = user_token
    _, user_b = second_user_token
    conv_resp = client.post("/api/conversations", json={"user_id": user_b}, headers=auth_header(token_a))
    conversation_id = conv_resp.get_json()["conversation_id"]

    data = {"file": (io.BytesIO(b"data"), "../../etc/passwd.txt"),
            "context_type": "conversation", "context_id": conversation_id}
    resp = client.post("/api/files", data=data, headers=auth_header(token_a), content_type="multipart/form-data")
    assert resp.status_code == 400


def test_oversized_file_rejected(client, user_token, second_user_token, app):
    token_a, _ = user_token
    _, user_b = second_user_token
    conv_resp = client.post("/api/conversations", json={"user_id": user_b}, headers=auth_header(token_a))
    conversation_id = conv_resp.get_json()["conversation_id"]

    from app.utils.file_validation import MAX_FILE_SIZE_BYTES
    big_content = b"a" * (MAX_FILE_SIZE_BYTES + 1)
    data = {"file": (io.BytesIO(big_content), "big.txt"),
            "context_type": "conversation", "context_id": conversation_id}
    resp = client.post("/api/files", data=data, headers=auth_header(token_a), content_type="multipart/form-data")
    assert resp.status_code == 400
    assert resp.get_json()["code"] == "file_too_large"


def test_group_file_transfer(client, user_token, second_user_token, third_user_token):
    token_a, user_a = user_token
    token_b, user_b = second_user_token
    _, user_c = third_user_token

    group_resp = client.post("/api/groups", json={"group_name": "Team", "member_ids": [user_b, user_c]},
                              headers=auth_header(token_a))
    group_id = group_resp.get_json()["group_id"]

    data = {"file": (io.BytesIO(b"team asset"), "asset.png"),
            "context_type": "group", "context_id": group_id}
    upload_resp = client.post("/api/files", data=data, headers=auth_header(token_a), content_type="multipart/form-data")
    assert upload_resp.status_code == 201
    file_id = upload_resp.get_json()["file_id"]

    download_resp = client.get(f"/api/files/{file_id}/download", headers=auth_header(token_b))
    assert download_resp.status_code == 200
    assert download_resp.data == b"team asset"
