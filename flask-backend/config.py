import os

SECRET_KEY = os.getenv("JWT_SECRET", "supersecretkey")

DB_PATH = os.getenv("MEETINGS_DB_PATH", "meetings.db")

RASA_URL = os.getenv("RASA_URL", "http://localhost:5005")
RASA_WEBHOOK_URL = f"{RASA_URL}/webhooks/rest/webhook"

SCHEDULER_API_URL = os.getenv(
    "SCHEDULER_API_URL",
    "http://localhost:8000/api/meetings/schedule"
)
