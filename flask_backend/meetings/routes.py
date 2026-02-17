"""Meeting scheduling and history routes for Flask API."""

from flask import Blueprint, request, jsonify
from flask_backend.decorators import token_required
from flask_backend.database import get_connection
from datetime import datetime

import json
import dateparser

meetings_bp = Blueprint("meetings", __name__)


def _json_body():
    """Safely read a JSON object body; return None for invalid/non-object payloads."""
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None


def normalize_meeting(payload):
    """Validate and normalize meeting payload into DB-ready values."""
    date_parsed = dateparser.parse(payload.get("date", ""), settings={"PREFER_DATES_FROM": "future"})
    time_parsed = dateparser.parse(payload.get("time", ""))

    if not date_parsed or not time_parsed:
        raise ValueError("Invalid date or time")

    if date_parsed.date() < datetime.now().date():
        raise ValueError("Date is in the past")

    platform = (payload.get("platform") or "").strip()
    platform_defaulted = False
    if not platform:
        platform = "Google Meet"
        platform_defaulted = True

    participants = payload.get("participants", [])
    if isinstance(participants, str):
        participants = [p.strip() for p in participants.split(",") if p.strip()]
    if not isinstance(participants, list):
        participants = []

    return {
        "date": date_parsed.date().isoformat(),
        "time": time_parsed.strftime("%H:%M"),
        "platform": platform,
        "platform_defaulted": platform_defaulted,
        "participants": participants,
        "reminder_time": payload.get("reminder_time"),
    }


@meetings_bp.route("/schedule", methods=["POST"])
@token_required
def schedule(current_user):
    """Persist a scheduled meeting for the authenticated user."""
    body = _json_body()
    if body is None:
        return jsonify({"error": "Invalid JSON body"}), 400

    try:
        normalized = normalize_meeting(body)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO meetings
            (created_at, user_id, date, time, platform, participants, reminder_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.utcnow().isoformat(),
            current_user[0],
            normalized["date"],
            normalized["time"],
            normalized["platform"],
            json.dumps(normalized["participants"]),
            normalized["reminder_time"],
        ))

        meeting_id = cursor.lastrowid

    response = {"meeting_id": meeting_id, **normalized}
    if normalized["platform_defaulted"]:
        response["platform_message"] = "Platform not provided. Choosing Google Meet as the default platform."
    return jsonify(response)


@meetings_bp.route("/history", methods=["GET"])
@token_required
def history(current_user):
    """Return meeting history for the authenticated user ordered newest-first."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, created_at, date, time, platform, participants, reminder_time
            FROM meetings
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (current_user[0],),
        ).fetchall()

    items = []
    for row in rows:
        participants = []
        try:
            parsed = json.loads(row[5]) if row[5] else []
            if isinstance(parsed, list):
                participants = parsed
        except (TypeError, ValueError):
            participants = []

        items.append({
            "id": row[0],
            "created_at": row[1],
            "date": row[2],
            "time": row[3],
            "platform": row[4],
            "participants": participants,
            "reminder_time": row[6],
        })

    return jsonify({"items": items})
