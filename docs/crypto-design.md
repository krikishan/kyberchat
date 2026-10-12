# Cryptographic Design

## Terminology (used consistently everywhere in this codebase)
- **ML-KEM-768** (FIPS 203): a post-quantum *Key Encapsulation Mechanism*. It establishes
  a shared secret between two parties. It does **not** encrypt messages.
- **HKDF** (RFC 5869): a *key derivation function*. It turns the ML-KEM shared secret into
  an application-specific AES key. It does not encrypt anything either.
- **AES-256-GCM**: *symmetric authenticated encryption*. This is what actually encrypts
  message and file content, using the key HKDF derived.
- **RSA-3072-OAEP**: classical public-key cryptography, used here only as a benchmarking
  comparison (see below) — not part of the real message path.

## Message/file encryption pipeline
```
ML-KEM encapsulation → shared secret → HKDF(SHA-256) → AES-256-GCM session key
                                                              |
                                                    encrypt message/file
```
Implementation: `backend/app/crypto/mlkem.py`, `hkdf.py`, `aes_gcm.py`.

## HKDF parameters
- Hash: SHA-256
- Salt: fresh random 32 bytes per key-establishment event, transmitted (not secret)
- Info: `"kyberchat-v1" | conversation_or_group_id` — binds the derived key to one
  conversation/group so a key can never be replayed into a different context.

## Public-key trust model (and its limits)
This is an authenticated-backend-key-directory model, not a full PKI or Signal-style
protocol:
- Each user's ML-KEM public key is generated server-side at account creation and stored
  in `key_metadata`, tied to their authenticated account.
- A sender fetches the recipient's public key from this backend-authenticated directory —
  trust in the key's authenticity rests on trust in the backend/database, not on
  independent out-of-band verification (no safety numbers / key-fingerprint verification
  UI is implemented in this college-project scope).
- **Limitation**: a compromised backend could substitute a public key (a MITM at the
  directory level). This is documented and accepted as an academic-prototype limitation —
  this is *not* claimed to be production-grade end-to-end-encryption trust infrastructure.

## Private key storage
- ML-KEM and RSA private keys are stored server-side (required for this architecture,
  since there is no persistent client-side key storage in a stateless web session).
- Private keys are never returned by any API response, never logged, never sent to Groq,
  and never committed to the repository.
- Key metadata (id, fingerprint, version, algorithm, created_at) is stored separately
  from the secret key material itself.

## Group chat key strategy
Each group has one active session key, established via hybrid ML-KEM broadcast key
wrapping (implemented in `backend/app/crypto/session_manager.py`, shared with 1:1
conversations):
1. Generate a fresh random 32-byte session key for the context (conversation/group) and version.
2. For **each current member independently**: ML-KEM-encapsulate against *their own*
   public key, HKDF-derive a per-member wrapping key from that member's shared secret,
   and AES-256-GCM-encrypt the session key under it. Every member gets a different
   wrapped copy, openable only with their own ML-KEM private key — this is not one
   hard-coded key for every group.
3. To read a message, a member decapsulates their own wrapped entry, re-derives the
   wrapping key, and unwraps the same underlying session key everyone else has.

Verified behaviour on membership change (see `backend/tests/test_groups.py`):
- **Join**: a new session-key version is generated and wrapped for the *current*
  member list, including the new member. The new member is never given a wrapped
  copy of any earlier version, so they cannot decrypt history from before they
  joined (proven by `test_new_member_cannot_read_history_before_joining`).
- **Leave / removal**: same rotation, wrapped only for members who remain. The
  removed member gets no wrapped copy of the new version, so they cannot decrypt
  anything sent afterward (proven by `test_removed_member_loses_group_access`, and
  route-level authorization also drops them from the group entirely).
- Older wrapped entries for members who were present at the time are not deleted,
  so a still-current member can always decrypt everything sent while they were a
  member — this is a documented simplification, not a full MLS-style ratchet with
  backward secrecy for messages sent *before* a member joined an earlier version.

## RSA comparison
RSA-3072-OAEP key-wrapping is benchmarked against ML-KEM-768 encapsulation as the fair
classical analogue of "establish a shared secret" (see
`experiments/mlkem_vs_rsa_benchmark.py` and `experiments/results/benchmark_results.json`
for real, measured, non-fabricated timings and payload sizes from this environment).

## What this is not
- Not a formally verified or audited cryptographic implementation.
- Not a full Signal-protocol equivalent (no double ratchet, no perfect forward secrecy
  beyond per-session key rotation, no out-of-band key verification UI).
- Not resistant to a fully compromised backend (trust model above).

## File storage note
Encrypted files are stored as a binary field directly inside each file's MongoDB
document (via the same AES-256-GCM session-key encryption as messages), capped at
10MB per file to stay within MongoDB's 16MB BSON document limit. This is a deliberate
college-project simplification — no GridFS or external object storage dependency,
and it works unmodified from stateless serverless functions (Vercel). A production
system with larger files would use GridFS or object storage (e.g. S3) referenced by
a `storage_reference`, which is already how the metadata schema is shaped.
