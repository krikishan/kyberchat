"""
Vercel serverless entrypoint. Vercel's Python runtime looks for a WSGI-
compatible `app` object in this file when routed to by vercel.json.

Important serverless caveats (documented fully in docs/deployment.md and
docs/security.md — spec section 65):
  - Each cold start creates a fresh process, so Flask-Limiter's default
    in-memory rate-limit storage resets per cold start / is not shared
    across concurrent invocations. For a real production deployment behind
    real traffic, back the limiter with Redis (`storage_uri` on Limiter).
    For this college-project scope, in-memory limiting still works
    correctly within a single warm instance.
  - MongoClient connection reuse only helps within a warm container;
    pymongo's own pooling still applies per-process.
  - There is no persistent local filesystem — this app never writes to
    disk outside of the request/response cycle, by design (files are
    stored as encrypted binary in MongoDB, not on disk).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import create_app  # noqa: E402

app = create_app()
