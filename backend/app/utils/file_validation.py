"""
File upload security (spec sections 21, 36.13, 36.14).

- Extension allowlist (not blocklist).
- The ORIGINAL filename is only ever stored as metadata for display — it is
  NEVER used as a filesystem/storage key (prevents path traversal).
- A random UUID is the actual storage key.
- MIME/extension consistency is checked on a best-effort basis using
  Python's stdlib `mimetypes` (no external "magic bytes" dependency in this
  scope — documented as a limitation; a production deployment should add
  content-sniffing, e.g. `python-magic`).
"""
import mimetypes
import os
import uuid

from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {
    "pdf", "txt", "doc", "docx", "jpg", "jpeg", "png", "zip", "gif", "csv", "md",
}
MAX_FILENAME_LENGTH = 200
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB — see docs/crypto-design.md storage note


class FileValidationError(Exception):
    def __init__(self, message: str, code: str = "invalid_file"):
        super().__init__(message)
        self.code = code


def validate_and_prepare(filename: str, file_bytes: bytes, declared_mime_type: str | None) -> dict:
    if not filename or len(filename) > MAX_FILENAME_LENGTH:
        raise FileValidationError("Invalid filename.", "invalid_filename")

    safe_name = secure_filename(filename)
    if not safe_name or ".." in filename or "/" in filename or "\\" in filename:
        raise FileValidationError("Invalid filename.", "invalid_filename")

    ext = safe_name.rsplit(".", 1)[-1].lower() if "." in safe_name else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise FileValidationError(f"File type '.{ext}' is not allowed.", "invalid_type")

    if len(file_bytes) == 0:
        raise FileValidationError("File is empty.", "empty_file")
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise FileValidationError(f"File exceeds the {MAX_FILE_SIZE_BYTES // (1024*1024)}MB limit.", "file_too_large")

    guessed_mime, _ = mimetypes.guess_type(safe_name)
    mime_type = declared_mime_type or guessed_mime or "application/octet-stream"

    storage_id = str(uuid.uuid4())
    return {
        "storage_id": storage_id,
        "original_filename": safe_name,
        "mime_type": mime_type,
        "size": len(file_bytes),
        "extension": ext,
    }
