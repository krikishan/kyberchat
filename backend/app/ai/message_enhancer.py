"""
Groq-based AI Message Enhancer (spec section 10).

Hard boundary: this module NEVER touches encryption, keys, passwords, or
authentication. It receives only the plaintext message text the user typed
(before encryption) and an enhancement style, and returns a suggested
rewrite. The caller (route) is responsible for never sending anything else
here, and for requiring the user's explicit approval before the enhanced
text is ever encrypted/sent.
"""
from __future__ import annotations

ENHANCEMENT_STYLES = {
    "professional": "Rewrite the message to sound professional and businesslike, while preserving its exact meaning.",
    "formal": "Rewrite the message in a formal register, while preserving its exact meaning.",
    "friendly": "Rewrite the message in a warm, friendly tone, while preserving its exact meaning.",
    "concise": "Rewrite the message to be as concise as possible, while preserving its exact meaning.",
    "clear": "Rewrite the message to be clearer and easier to understand, while preserving its exact meaning.",
}

MAX_INPUT_CHARS = 2000


class AIEnhancementError(Exception):
    pass


def enhance_message(groq_client, text: str, style: str) -> str:
    if not text or not text.strip():
        raise AIEnhancementError("Message text is required.")
    if len(text) > MAX_INPUT_CHARS:
        raise AIEnhancementError(f"Message is too long to enhance (max {MAX_INPUT_CHARS} characters).")
    if style not in ENHANCEMENT_STYLES:
        raise AIEnhancementError(f"Unknown style. Choose one of: {', '.join(ENHANCEMENT_STYLES)}.")

    if groq_client is None:
        raise AIEnhancementError("AI enhancement is temporarily unavailable. You can still send your original message.")

    instruction = ENHANCEMENT_STYLES[style]
    try:
        response = groq_client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"{instruction} Reply with ONLY the rewritten message text — "
                        "no preamble, no quotes, no explanation."
                    ),
                },
                {"role": "user", "content": text},
            ],
            max_tokens=500,
            temperature=0.4,
            timeout=8,
        )
    except Exception as exc:
        raise AIEnhancementError("AI enhancement is temporarily unavailable. You can still send your original message.") from exc

    enhanced = (response.choices[0].message.content or "").strip()
    if not enhanced:
        raise AIEnhancementError("AI enhancement returned an empty result. You can still send your original message.")
    return enhanced
