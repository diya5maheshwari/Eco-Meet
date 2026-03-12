"""Flask proxy routes for Rasa chat and parse APIs."""
import json
from datetime import datetime

from flask_backend.google_calendar_service import create_google_meet_link
from flask_backend.notifications import send_meeting_notifications
from flask_backend.meetings.routes import normalize_meeting
from flask_backend.database import get_connection
from flask import Blueprint, request, jsonify
import requests
from flask_backend.config import RASA_WEBHOOK_URL, RASA_URL
from flask_backend.decorators import token_required


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


# ---------------- HEALTH CHECK ----------------
@rasa_bp.route("/health", methods=["GET"])
def health():
    """Check if Flask can reach Rasa server."""
    try:
        resp = requests.get(f"{RASA_URL}/status", timeout=3)
        if resp.status_code == 200:
            return jsonify({"status": "ok", "rasa": "connected"})
    except requests.RequestException:
        pass

    return jsonify({"status": "ok", "rasa": "disconnected"}), 200


# ---------------- CHAT ----------------
@rasa_bp.route("/chat", methods=["POST"])
@token_required
def chat(current_user):

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

    # 🔥 HERE WE HANDLE MEETING CREATION
    new_messages = []

    for message in messages:
        new_messages.append(message)

        custom = message.get("custom") if isinstance(message, dict) else None

        if isinstance(custom, dict) and custom.get("type") == "meeting_data":

            meeting_info = create_google_meet_link(
                custom.get("date"),
                custom.get("time"),
                custom.get("participants", [])
            )

            try:
                normalized = normalize_meeting({
                    "date": custom.get("date"),
                    "time": custom.get("time"),
                    "platform": meeting_info.get("platform", custom.get("platform")),
                    "participants": custom.get("participants", []),
                    "reminder_time": custom.get("reminder_time"),
                })

                with get_connection() as conn:
                    cursor = conn.execute(
                        """
                        INSERT INTO meetings
                        (created_at, user_id, date, time, platform, participants, reminder_time)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            datetime.utcnow().isoformat(),
                            current_user[0],
                            normalized["date"],
                            normalized["time"],
                            normalized["platform"],
                            json.dumps(normalized["participants"]),
                            normalized["reminder_time"],
                        ),
                    )
                    meeting_id = cursor.lastrowid

                new_messages.append({
                    "custom": {
                        "type": "meeting_saved",
                        "meeting_id": meeting_id,
                        "date": normalized["date"],
                        "time": normalized["time"],
                        "platform": normalized["platform"],
                        "participants": normalized["participants"],
                        "reminder_time": normalized["reminder_time"],
                    }
                })
            except Exception as exc:
                print(f"Failed to save meeting: {exc}")

            try:
                send_meeting_notifications(
                    user_id=current_user[0],
                    date=custom.get("date"),
                    time=custom.get("time"),
                    platform=meeting_info.get("platform", "Google Meet"),
                    meeting_link=meeting_info.get("meeting_link", ""),
                    participants=custom.get("participants", []),
                    reminder_time=custom.get("reminder_time"),
                )
            except Exception as exc:
                print(f"Failed to send WhatsApp notifications: {exc}")

            new_messages.append({
                "text": f"Your meeting is scheduled! Here is your link:\n{meeting_info['meeting_link']}"
            })

            new_messages.append({
                "custom": {
                    "type": "meeting_link",
                    **meeting_info
                }
            })

    return jsonify(new_messages)


# ---------------- NLU PARSE ----------------
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
