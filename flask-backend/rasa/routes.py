"""Flask proxy routes for Rasa chat and parse APIs."""

from flask import Blueprint, request, jsonify
from config import RASA_WEBHOOK_URL, RASA_URL
from decorators import token_required
import requests

rasa_bp = Blueprint("rasa", __name__)


def _json_body():
    """Safely read a JSON object body; return None for invalid/non-object payloads."""
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None


def _default_rasa_offline_message():
    """Fallback bot response returned when Rasa is unavailable."""
    return [
        {
            "text": "Rasa service is currently unavailable. Please try again in a moment."
        }
    ]


@rasa_bp.route("/chat", methods=["POST"])
@token_required
def chat(current_user):
    """Forward user chat message to Rasa and normalize fallback/default behavior."""
    body = _json_body()
    if body is None:
        return jsonify({"error": "invalid JSON body"}), 400

    text = (body.get("text") or "").strip()

    if not text:
        return jsonify({"error": "text required"}), 400

    try:
        resp = requests.post(
            RASA_WEBHOOK_URL,
            json={"sender": str(current_user[0]), "message": text},
            timeout=10
        )
        resp.raise_for_status()
        messages = resp.json()
    except (requests.RequestException, ValueError):
        return jsonify(_default_rasa_offline_message()), 200

    if not isinstance(messages, list):
        return jsonify(_default_rasa_offline_message()), 200

    # If Rasa emits meeting payload without platform, inject user-facing default notice.
    platform_notice_added = False
    for message in messages:
        custom = message.get("custom") if isinstance(message, dict) else None
        if isinstance(custom, dict) and custom.get("type") == "meeting_data":
            if not (custom.get("platform") or "").strip():
                custom["platform"] = "Google Meet"
                platform_notice_added = True

    if platform_notice_added:
        messages.append({
            "text": "Platform was not provided, choosing Google Meet as the default platform."
        })

    return jsonify(messages)


@rasa_bp.route("/nlu/parse", methods=["POST"])
def nlu_parse():
    """Forward raw text to Rasa NLU parse endpoint."""
    body = _json_body()
    if body is None:
        return jsonify({"error": "invalid JSON body"}), 400

    text = (body.get("text") or "").strip()
    if not text:
        return jsonify({"error": "text required"}), 400

    try:
        resp = requests.post(
            f"{RASA_URL}/model/parse",
            json={"text": text},
            timeout=5
        )
        resp.raise_for_status()
        return jsonify(resp.json())
    except (requests.RequestException, ValueError):
        return jsonify({
            "error": "Rasa parse service unavailable",
            "text": text,
            "intent": {"name": "nlu_fallback", "confidence": 0.0},
            "entities": []
        }), 503
