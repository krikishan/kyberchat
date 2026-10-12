# Security Model

Cryptographic design/trust model/limitations live in `docs/crypto-design.md`. This
document covers application/web-level security (spec section 36).

## Authentication & session model
- Passwords hashed with Argon2id (`argon2-cffi`), never stored or logged in plaintext.
- JWT bearer tokens (not cookies) — so CSRF (spec 36.9) does not apply here: CSRF
  exploits a browser automatically attaching cookies to cross-site requests; a bearer
  token in an `Authorization` header is never attached automatically by the browser,
  so a malicious site cannot ride a logged-in session the way it could with cookies.
- Every token carries a `session_version` claim, checked against the user's current
  value on every request. Logout and password change both increment it, immediately
  invalidating every previously issued token — verified by
  `test_auth.py::test_logout_invalidates_token` and `::test_change_password_invalidates_old_token`.
- Login errors are generic ("Invalid username or password.") regardless of whether the
  account exists or the password was wrong, to avoid user enumeration.

## Authorization
- Every admin endpoint checks the caller's role **server-side** via `@require_role("admin")`
  — never inferred from the frontend. Verified by `test_admin.py::test_regular_user_cannot_add_members`.
- Every conversation/group/file access checks membership/participation server-side
  before returning data (`require_participant`, `require_member`, `_resolve_context`).
  Verified by IDOR-style tests in `test_conversations.py`, `test_groups.py`, `test_files.py`
  (non-participant/non-member gets 403 on both read and write).

## Input validation & injection protection
- Email format validated with `email-validator` (RFC-compliant), independent of any
  AI-assisted parsing.
- MongoDB queries are built from typed Python values via pymongo's query API — never
  string-concatenated into a query, so NoSQL injection via operator injection
  (`{"$ne": null}` style payloads) is not possible through normal JSON body parsing
  the way it is when a raw string is passed straight into a `$where` or similar.
- File uploads: extension allowlist, filename sanitization (path traversal blocked —
  verified by `test_files.py::test_path_traversal_filename_rejected`), size cap.

## XSS
- The backend never renders HTML from user input; all API responses are JSON. The
  React frontend renders message content as text (JSX escapes by default — no
  `dangerouslySetInnerHTML` is used anywhere in the frontend), so stored message
  content cannot execute as HTML/JS in another user's browser.

## Rate limiting
Flask-Limiter applied to sensitive endpoints: login (10/min), password change (5/min),
member creation (30/min), bulk preview (10/min) and confirm (5/min), AI enhance
(20/min), messages (60/min), group membership changes (20/min), file upload (20/min)
and download (60/min). See `docs/deployment.md` for the serverless in-memory-storage
caveat.

## Security headers
Set on every response (`app/__init__.py`): `X-Content-Type-Options: nosniff`,
`Referrer-Policy: strict-origin-when-cross-origin`, `X-Frame-Options: DENY`,
`Content-Security-Policy: default-src 'self'`, and `Strict-Transport-Security`
outside development mode.

## CORS
Configured to the single `FRONTEND_URL` origin — never `*` — for all authenticated APIs.

## Secrets
`SECRET_KEY`, `JWT_SECRET_KEY`, `MONGODB_URI`, `GROQ_API_KEY`, `MAIL_PASSWORD` are read
only from environment variables (`app/config.py` fails fast if the required ones are
missing) and are never returned in any API response, logged, or committed (`.gitignore`).

## Error handling & logging
A global Flask error handler logs full exception detail server-side only and returns
a generic `{"error": "Service temporarily unavailable."}` to the client — no stack
traces, file paths, or internal config ever reach a response. SMTP failures similarly
log a generic message without the recipient/credential detail (`app/email/mailer.py`).

## Audit logging
`audit_logs` records: user_created, bulk_user_creation, user_status_changed,
login_success, login_failure, logout, password_changed — with the acting user and a
server timestamp, never passwords/keys/tokens/plaintext message content.

## What is explicitly NOT claimed
- Not formally verified/audited cryptography or infrastructure.
- Not equivalent to a full Signal-protocol deployment (see `docs/crypto-design.md`).
- Not resistant to a fully compromised backend/host (an attacker with `SECRET_KEY` and
  DB access could decrypt stored private keys and impersonate the key directory).
- Rate limiting is not distributed/durable across a serverless fleet in this scope.
- No independent penetration test has been performed; the security properties above
  are validated by the automated test suite (`backend/tests/`), which is not a
  substitute for one.
