# import json
# import os
# import sqlite3
# from datetime import datetime
# from typing import Any, Dict

# import dateparser
# import requests
# from flask import Flask, jsonify, request

# DB_PATH = os.getenv("MEETINGS_DB_PATH", "meetings.db")
# RASA_URL = os.getenv("RASA_URL", "http://localhost:5005")
# RASA_WEBHOOK_URL = os.getenv("RASA_WEBHOOK_URL", f"{RASA_URL}/webhooks/rest/webhook")

# app = Flask(__name__)


# def _init_db() -> None:
#     with sqlite3.connect(DB_PATH) as conn:
#         conn.execute(
#             """
#             CREATE TABLE IF NOT EXISTS meetings (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 created_at TEXT NOT NULL,
#                 user_id TEXT,
#                 date TEXT NOT NULL,
#                 time TEXT NOT NULL,
#                 platform TEXT NOT NULL,
#                 participants TEXT NOT NULL,
#                 reminder_time TEXT
#             )
#             """
#         )


# def _normalize_meeting(payload: Dict[str, Any]) -> Dict[str, Any]:
#     date_raw = payload.get("date", "")
#     time_raw = payload.get("time", "")
#     date_parsed = dateparser.parse(date_raw, settings={"PREFER_DATES_FROM": "future"})
#     time_parsed = dateparser.parse(time_raw)
#     if not date_parsed or not time_parsed:
#         raise ValueError("Invalid date or time")

#     if date_parsed.date() < datetime.now().date():
#         raise ValueError("Date is in the past")

#     return {
#         "user_id": payload.get("user_id"),
#         "date": date_parsed.date().isoformat(),
#         "time": time_parsed.strftime("%H:%M"),
#         "platform": payload.get("platform"),
#         "participants": payload.get("participants", []),
#         "reminder_time": payload.get("reminder_time"),
#     }


# @app.post("/nlu/parse")
# def nlu_parse():
#     body = request.get_json(force=True) or {}
#     text = body.get("text", "")
#     if not text:
#         return jsonify({"error": "text is required"}), 400

#     resp = requests.post(f"{RASA_URL}/model/parse", json={"text": text}, timeout=5)
#     return jsonify(resp.json())


# @app.post("/chat")
# def chat():
#     body = request.get_json(force=True) or {}
#     text = body.get("text", "")
#     sender = body.get("sender", "mobile_user")
#     if not text:
#         return jsonify({"error": "text is required"}), 400

#     resp = requests.post(
#         RASA_WEBHOOK_URL,
#         json={"sender": sender, "message": text},
#         timeout=10,
#     )
#     return jsonify(resp.json())


# @app.post("/schedule")
# def schedule():
#     body = request.get_json(force=True) or {}
#     try:
#         normalized = _normalize_meeting(body)
#     except ValueError as exc:
#         return jsonify({"error": str(exc)}), 400

#     _init_db()
#     with sqlite3.connect(DB_PATH) as conn:
#         cursor = conn.execute(
#             """
#             INSERT INTO meetings (created_at, user_id, date, time, platform, participants, reminder_time)
#             VALUES (?, ?, ?, ?, ?, ?, ?)
#             """,
#             (
#                 datetime.utcnow().isoformat(),
#                 normalized["user_id"],
#                 normalized["date"],
#                 normalized["time"],
#                 normalized["platform"],
#                 json.dumps(normalized["participants"]),
#                 normalized["reminder_time"],
#             ),
#         )
#         meeting_id = cursor.lastrowid

#     return jsonify({"meeting_id": meeting_id, **normalized})


# if __name__ == "__main__":
#     _init_db()
#     app.run(host="0.0.0.0", port=8000, debug=True)
from flask import Flask, request
from flask_cors import CORS

from flask_backend.database import init_db
from flask_backend.auth.routes import auth_bp
from flask_backend.meetings.routes import meetings_bp
from flask_backend.contacts.routes import contacts_bp
from flask_backend.rasa.routes import rasa_bp
from flask_backend.database import init_db


app = Flask(__name__)

# Enable cross-origin requests for mobile/web clients using Bearer tokens.
CORS(app)

# Ensure SQLite tables exist before serving traffic.
init_db()

@app.before_request
def log_request_info():
    print(f"Request: {request.method} {request.url} from {request.remote_addr}")

app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(meetings_bp, url_prefix="/api/meetings")
app.register_blueprint(contacts_bp, url_prefix="/api/contacts")
app.register_blueprint(rasa_bp, url_prefix="/api")

if __name__ == "__main__":
    # Local development runner.
    app.run(host="0.0.0.0", port=8000, debug=True)

