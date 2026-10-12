# API Reference

Base URL: `BACKEND_URL` (e.g. `https://kyberchat-backend.vercel.app`). All request/response
bodies are JSON unless noted. Authenticated endpoints require `Authorization: Bearer <token>`.

## Auth (`/api/auth`)
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/login` | — | `{username, password}` → `{token, user}`. Rate limited (10/min). |
| POST | `/logout` | user | Invalidates the current token (bumps session version). |
| POST | `/change-password` | user | `{current_password, new_password}` → `{message, token}`. Invalidates old sessions. Rate limited (5/min). |
| GET | `/me` | user | Current user profile. |

## Admin — Team Management (`/api/admin`, Admin role only)
| Method | Path | Description |
|---|---|---|
| POST | `/users` | `{name, email}` → creates account, emails credentials. Rate limited (30/min). |
| GET | `/users` | Paginated member list (`?page=&page_size=`). |
| GET | `/users/:id` | Single member detail. |
| PATCH | `/users/:id` | `{status: "active"\|"inactive"}` — activate/deactivate, invalidates their sessions. |
| POST | `/users/bulk/preview` | `{raw_text}` → AI-assisted parse + deterministic validation preview (never creates accounts). Rate limited (10/min). |
| POST | `/users/bulk/confirm` | `{emails: [...]}` → creates exactly the confirmed list. Rate limited (5/min), max batch size configurable (`BULK_ADD_MAX_BATCH`, default 50). |

## Team Directory (`/api/team`, any authenticated user)
| Method | Path | Description |
|---|---|---|
| GET | `/members` | Basic directory (id, name, username, role) excluding the caller and sensitive fields. |

## Individual Chat (`/api/conversations`)
| Method | Path | Description |
|---|---|---|
| POST | `` | `{user_id}` → creates or returns the existing 1:1 conversation. |
| GET | `` | List the caller's conversations. |
| POST | `/:id/messages` | `{content}` → encrypts and stores. Rate limited (60/min). Participants only. |
| GET | `/:id/messages` | Decrypted message list. Participants only. |

## Group Chat (`/api/groups`)
| Method | Path | Description |
|---|---|---|
| POST | `` | `{group_name, member_ids}` → creates group + initial session key. |
| GET | `` | List the caller's groups. |
| GET | `/:id` | Group detail. Members only. |
| POST | `/:id/members` | `{user_id}` → add member + key rotation. Creator only. Rate limited (20/min). |
| DELETE | `/:id/members/:userId` | Remove member + key rotation. Creator only. Rate limited (20/min). |
| POST | `/:id/messages` | `{content}` → encrypts and stores. Members only. Rate limited (60/min). |
| GET | `/:id/messages` | Decrypted message list; messages from before a member joined show `accessible: false`. |

## Files (`/api/files`)
| Method | Path | Description |
|---|---|---|
| POST | `` | `multipart/form-data`: `file`, `context_type` (`conversation`\|`group`), `context_id`. Rate limited (20/min). |
| GET | `?context_type=&context_id=` | List files for a context. Authorized members/participants only. |
| GET | `/:id` | File metadata. |
| GET | `/:id/download` | Decrypted file bytes with safe `Content-Disposition`. Rate limited (60/min). |

## AI Message Enhancer (`/api/ai`)
| Method | Path | Description |
|---|---|---|
| POST | `/enhance` | `{text, style}` → `{original, enhanced, style}`. Available to Admin and Regular Users alike. Never auto-sends. Rate limited (20/min). |
| GET | `/enhance/styles` | List of valid style keys. |

## Cryptography (`/api/crypto`)
| Method | Path | Description |
|---|---|---|
| POST | `/simulation` | `{message}` → runs the real ML-KEM→HKDF→AES pipeline, returns per-stage timing + safe metadata. |
| POST | `/test` | Quick pass/fail self-test of the same pipeline. |

## Performance (`/api/performance`)
| Method | Path | Description |
|---|---|---|
| GET | `` | Aggregated real stats per algorithm/operation, or `{"status": "Not measured"}`. |
| POST | `/run` | Admin only. `{trials}` (max 50/request) → runs real benchmarks, stores results. |
| GET | `/export` | Admin only. CSV of every stored measurement. |

## Health (`/api/health`)
| Method | Path | Description |
|---|---|---|
| GET | `` | `{overall_status, services: {backend_api, database, email_service, groq_ai, authentication}}` — each actually checked, never assumed. |

## Error shape
Every error response is `{"error": "human-readable message", "code": "machine_code"}` (code
omitted on a few generic/security-sensitive paths, e.g. login, to avoid leaking detail).
Standard status codes: 400 validation, 401 unauthenticated, 403 unauthorized, 404 not found,
500 unexpected (never includes a stack trace or internal detail).
