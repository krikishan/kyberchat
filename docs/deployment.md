# Deployment Runbook

This deploys the backend and frontend as two separate Vercel projects from one
GitHub repo — the simplest reliable setup for a Flask API + a static Vite frontend.

## 1. MongoDB Atlas
1. Create a free M0 cluster at https://cloud.mongodb.com.
2. Database Access → add a database user with a strong, generated password
   (not your Atlas account password).
3. Network Access → for a college project, "Allow access from anywhere"
   (0.0.0.0/0) is the pragmatic choice since Vercel's serverless functions
   don't have static IPs; document this as an accepted trade-off (Atlas
   still requires the DB username/password and TLS).
4. Get the connection string ("Connect" → "Drivers") — this is your `MONGODB_URI`.
   It already includes `?retryWrites=true&w=majority`; the app enables `tls=True`
   explicitly as well (`backend/app/database/db.py`).

## 2. Groq API
1. Create a key at https://console.groq.com/keys.
2. This becomes `GROQ_API_KEY`. If you skip this, the app runs fine — the AI
   Message Enhancer just returns a clear "temporarily unavailable" message
   instead of crashing (verified by `test_ai_enhancer.py`).

## 3. Gmail SMTP (dedicated project account)
1. Create a dedicated Gmail account for the project (e.g.
   `kyberchat.project@gmail.com`) — don't use a personal account.
2. Enable 2-Step Verification on that account (required for App Passwords).
3. Google Account → Security → App Passwords → generate one for "Mail".
4. `MAIL_USERNAME` = the Gmail address, `MAIL_PASSWORD` = the 16-character
   App Password (not the account's login password).

## 4. Environment variables
Copy `.env.example` → `.env` locally for development. In Vercel, set the same
keys under Project → Settings → Environment Variables for **both** projects
where relevant:

**Backend project:**
```
MONGODB_URI, MONGODB_DB_NAME, SECRET_KEY, JWT_SECRET_KEY,
JWT_ACCESS_TOKEN_EXPIRES_MIN, GROQ_API_KEY, MAIL_USERNAME, MAIL_PASSWORD,
MAIL_SERVER, MAIL_PORT, MAIL_USE_TLS, FRONTEND_URL, BACKEND_URL, FLASK_ENV=production
```
Generate `SECRET_KEY` / `JWT_SECRET_KEY` with, e.g., `python -c "import secrets; print(secrets.token_hex(32))"`
— use two different random values, never reuse one.

**Frontend project:**
```
VITE_BACKEND_URL=https://<your-backend-project>.vercel.app
```

## 5. GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin <your-repo-url>
git push -u origin main
```
`.gitignore` already excludes `.env`, `node_modules/`, `__pycache__/`, etc.
Double-check `git status` shows no `.env` file before your first push.

## 6. Deploy the backend to Vercel
1. Vercel dashboard → New Project → import the repo → set **Root Directory**
   to `backend/`.
2. Vercel auto-detects `vercel.json` (Python runtime via `@vercel/python`,
   routing everything to `api/index.py`).
3. Add the backend environment variables (step 4).
4. Deploy. Note the resulting URL — this is `BACKEND_URL` / what the frontend's
   `VITE_BACKEND_URL` must point to.

**Known constraint**: `pqcrypto` ships prebuilt wheels for standard Linux
x86_64, which matches Vercel's Python build image — if a future PyPI release
changes this, the build step will need a source build environment instead;
watch the build logs on first deploy.

## 7. Deploy the frontend to Vercel
1. New Project → same repo → **Root Directory** = `frontend/`.
2. Vercel auto-detects Vite (or use the included `vercel.json`).
3. Set `VITE_BACKEND_URL` to the backend URL from step 6.
4. Deploy.

## 8. Configure production CORS and URLs
1. Back in the **backend** project's environment variables, set `FRONTEND_URL`
   to the frontend's actual Vercel URL, then redeploy the backend (CORS is
   configured from this single value in `app/__init__.py` — it only allows
   that one origin, never `*`, for authenticated APIs).
2. Confirm `BACKEND_URL` on the backend matches its own deployed URL (used in
   the credential email's login link).

## 9. Production test checklist
Run through each of these against the live URLs before calling the deployment done:
- [ ] Load the frontend URL — login page renders.
- [ ] Log in as the Team Admin (create this user directly in Atlas the first
      time — see "Bootstrapping the first Admin" below).
- [ ] Add a member → confirm the credential email arrives (real Gmail send).
- [ ] Log in as that new member with the temporary password → forced password
      change works → new session persists.
- [ ] Start an individual chat, send a message, confirm the recipient can read it.
- [ ] Create a group, send a message, remove a member, confirm they lose access.
- [ ] Upload and download a file.
- [ ] Use the AI Message Enhancer (requires `GROQ_API_KEY` to be set) — confirm
      it returns a real enhanced suggestion, not just the fallback error.
- [ ] Open the Encryption Simulation page — confirm it reports success.
- [ ] As Admin, run a benchmark on the Performance page — confirm real numbers
      populate (not all "Not measured").
- [ ] Check the System Health page — all services should show "Healthy" (Groq
      shows "Not configured" if you skipped that step, which is expected).

### Bootstrapping the first Admin
There is no signup flow (by design — spec: only the Admin adds members). Create
the first Team Admin user directly, once, via a short Python script run locally
against your real `MONGODB_URI`:
```python
# run once, locally, with your real .env loaded
from app import create_app
from app.auth.passwords import hash_password
from app.crypto.key_directory import generate_and_store_user_keys
import datetime

app = create_app()
with app.app_context():
    db = app.db
    now = datetime.datetime.utcnow()
    result = db.users.insert_one({
        "name": "Admin", "email": "admin@example.com", "username": "admin",
        "password_hash": hash_password("ChangeThisTemporaryPassword1!"),
        "role": "admin", "status": "active", "must_change_password": True,
        "session_version": 0, "created_at": now, "updated_at": now,
    })
    generate_and_store_user_keys(db, app.config["SECRET_KEY"], str(result.inserted_id))
    print("Admin created:", result.inserted_id)
```
Log in with that username/password once, then immediately change the password
(the app enforces this via `must_change_password`).

## Deployment limitations (documented per spec section 65)
- **Rate limiting**: in-memory, per-warm-instance only in this scope — not
  shared across concurrent serverless invocations. Fine for a college-project
  demo; a real production deployment should point Flask-Limiter at Redis.
- **No background workers**: everything here runs within the request/response
  cycle of a single serverless invocation — there is no long-running process,
  by design.
- **No local filesystem persistence**: files are stored as encrypted binary
  in MongoDB specifically so the app works statelessly on Vercel.
