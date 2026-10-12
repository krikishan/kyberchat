"""
Bulk member addition — parsing stage only (spec section 8).

IMPORTANT boundary: AI may assist with cleaning up messy pasted text (extra
punctuation, inconsistent separators, stray names next to emails), but it
is NEVER trusted to decide validity, authorization, or duplicates. Every
candidate — whether it came from the deterministic parser or from Groq's
suggestion — is re-validated by the same deterministic `email_validator`
check in user_service before anything is shown to the Admin as a preview,
and again before account creation. Groq cannot create accounts, cannot
bypass duplicate checks, and is never given database or authorization
access.
"""
import re

_EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")


def deterministic_extract(raw_text: str) -> list[str]:
    """Authoritative extraction: pull anything that looks like an email,
    regardless of separators (newlines, commas, semicolons, spaces)."""
    return _EMAIL_REGEX.findall(raw_text or "")


def ai_assisted_extract(raw_text: str, groq_client) -> list[str]:
    """
    Optional pass: ask Groq to help pull emails out of messy text (e.g. a
    pasted roster with names, titles, and emails jumbled together). If Groq
    is unavailable or errors, silently fall back to the deterministic
    extractor — bulk-add must keep working without AI.

    The AI's output is treated as untrusted candidate text only: it is run
    back through `deterministic_extract` (regex) so nothing the model
    "hallucinates" as an email can slip through as a bare string, and it
    still goes through full email_validator + duplicate checks downstream.
    """
    if groq_client is None:
        return deterministic_extract(raw_text)

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Extract every email address present in the user's text. "
                        "Reply with ONLY the email addresses, one per line, nothing else."
                    ),
                },
                {"role": "user", "content": raw_text[:4000]},
            ],
            max_tokens=1000,
            timeout=8,
        )
        ai_text = response.choices[0].message.content or ""
    except Exception:
        return deterministic_extract(raw_text)

    # Never trust the AI's text directly — re-extract with the deterministic regex.
    candidates = deterministic_extract(ai_text)
    return candidates or deterministic_extract(raw_text)


def build_preview(db, raw_emails: list[str], max_batch: int) -> dict:
    """Deterministic validation + duplicate detection. This function alone
    decides what is safe to create — never the AI extraction step above."""
    from app.services.user_service import normalize_email, validate_email_format, email_exists, UserCreationError

    if len(raw_emails) > max_batch:
        raise UserCreationError(f"Batch too large: max {max_batch} addresses per bulk request.", code="batch_too_large")

    seen_in_batch = set()
    valid, invalid, duplicates_in_batch, already_exists = [], [], [], []

    for raw in raw_emails:
        normalized = normalize_email(raw)
        try:
            clean = validate_email_format(normalized)
        except UserCreationError:
            invalid.append(raw)
            continue

        if clean in seen_in_batch:
            duplicates_in_batch.append(clean)
            continue
        seen_in_batch.add(clean)

        if email_exists(db, clean):
            already_exists.append(clean)
            continue

        valid.append(clean)

    return {
        "valid": valid,
        "invalid": invalid,
        "duplicates_in_batch": duplicates_in_batch,
        "already_exists": already_exists,
        "total_submitted": len(raw_emails),
        "will_create": len(valid),
    }
