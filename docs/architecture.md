# Architecture

```
Browser (React/Vite)
      |
      | HTTPS, Bearer JWT
      v
Flask backend (Vercel serverless function)
      |
      | TLS
      v
MongoDB Atlas
```

## Backend layout
```
backend/app/
  routes/        Flask blueprints - one per resource (auth, admin, conversations,
                 groups, files, ai, crypto, performance, health, team)
  services/      Business logic, independent of HTTP (user_service, conversation_service,
                 group_service, file_service, performance_service, crypto_simulation, audit_log)
  crypto/        mlkem.py, hkdf.py, aes_gcm.py, rsa_compare.py, session_manager.py
                 (hybrid group key wrapping), key_directory.py (public-key directory +
                 encrypted-at-rest private key storage)
  auth/          passwords.py (Argon2id, generation), tokens.py (JWT issuance/verification,
                 require_auth / require_role decorators)
  ai/            message_enhancer.py (Groq), bulk_parser.py (AI-assisted, deterministically
                 re-validated)
  email/         mailer.py (Gmail SMTP)
  database/      db.py (MongoDB connection, indexes)
  utils/         file_validation.py
```
Routes never contain business logic beyond request parsing and status-code mapping;
services never import Flask. This keeps the crypto/business logic testable without a
running HTTP server (see `backend/tests/`, all driven through `mongomock` + Flask's
test client).

## Data flow: sending an encrypted message
1. Client sends plaintext (already optionally AI-enhanced and user-approved) to
   `POST /conversations/:id/messages` or `POST /groups/:id/messages`.
2. The route calls the relevant service, which calls
   `session_manager.encrypt_for_context()`:
   - Resolves the sender's wrapped session key for the current version
     (decapsulating with their ML-KEM private key, HKDF-deriving the wrapping key,
     AES-256-GCM-unwrapping the actual session key).
   - AES-256-GCM-encrypts the message under that session key.
3. Only `{ciphertext, nonce, key_version}` plus routing metadata (sender, timestamp)
   is stored in MongoDB - never plaintext.
4. On read, the same chain runs in reverse for the requesting (authorized) user.

## Data flow: group membership change
`group_service.add_member` / `remove_member` update the `members` array, then call
`session_manager.establish_session()` again for the *current* member list - a fresh
random session key is generated and independently ML-KEM-wrapped per current member.
See `docs/crypto-design.md` for the full protocol and its documented limitations.

## Frontend layout
```
frontend/src/
  api/client.js        one fetch wrapper for every backend endpoint
  context/AuthContext   session state (token in sessionStorage, not localStorage)
  components/           Sidebar, Layout, MessageComposer (AI enhance UI), route guards
  pages/                 one file per screen
```

## Why these technology choices
- **ML-KEM via `pqcrypto`**: maintained PQClean bindings, not hand-rolled PQC math
  (spec requirement).
- **Files as encrypted binary in MongoDB, not GridFS/S3**: keeps the required stack
  (Flask + MongoDB Atlas) sufficient with no extra paid service, while still being
  genuinely deployable statelessly on Vercel. Capped at 10MB/file - see
  `docs/crypto-design.md`.
- **JWT over server-side sessions**: no server-side session store needed, which suits
  stateless serverless functions; session invalidation is handled via a
  `session_version` counter checked against each token's claim.
