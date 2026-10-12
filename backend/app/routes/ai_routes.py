from flask import Blueprint, current_app, jsonify, request

from app import limiter
from app.ai.message_enhancer import AIEnhancementError, ENHANCEMENT_STYLES, enhance_message
from app.auth.tokens import require_auth

ai_bp = Blueprint("ai", __name__)


@ai_bp.route("/enhance", methods=["POST"])
@require_auth
@limiter.limit("20 per minute")  # available to Admin AND Regular Users alike
def enhance():
    data = request.get_json(silent=True) or {}
    text = data.get("text", "")
    style = data.get("style", "clear")

    groq_client = getattr(current_app, "groq_client", None)
    try:
        enhanced = enhance_message(groq_client, text, style)
    except AIEnhancementError as exc:
        return jsonify({"error": str(exc)}), 503

    # Original is always returned alongside the suggestion — the frontend
    # must show both and require explicit user approval before sending;
    # this endpoint never sends anything anywhere by itself.
    return jsonify({"original": text, "enhanced": enhanced, "style": style})


@ai_bp.route("/enhance/styles", methods=["GET"])
@require_auth
def styles():
    return jsonify({"styles": list(ENHANCEMENT_STYLES.keys())})
