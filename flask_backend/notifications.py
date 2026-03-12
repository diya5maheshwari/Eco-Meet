"""WhatsApp notifications via Twilio plus reminder scheduling."""

from __future__ import annotations

import json
import os
import re
import threading
from datetime import datetime, timedelta
from typing import Dict, Iterable, List, Optional, Set, Tuple

from flask_backend.database import get_connection

try:
    from twilio.rest import Client
except Exception: 
    Client = None


DEFAULT_COUNTRY_CODE = (os.getenv("DEFAULT_COUNTRY_CODE") or "").strip()
TWILIO_ACCOUNT_SID = (os.getenv("TWILIO_ACCOUNT_SID") or "").strip()
TWILIO_AUTH_TOKEN = (os.getenv("TWILIO_AUTH_TOKEN") or "").strip()
TWILIO_WHATSAPP_FROM = (os.getenv("TWILIO_WHATSAPP_FROM") or "").strip()
TWILIO_MESSAGING_SERVICE_SID = (os.getenv("TWILIO_MESSAGING_SERVICE_SID") or "").strip()

_SCHEDULED: List[threading.Timer] = []
_TWILIO_CLIENT: Optional[Client] = None


def _parse_list(value: object) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return []
        try:
            loaded = json.loads(raw)
            if isinstance(loaded, list):
                return [str(v).strip() for v in loaded if str(v).strip()]
        except (TypeError, ValueError):
            pass
        return [v.strip() for v in raw.split(",") if v.strip()]
    return []


def _normalize_number(raw: str) -> str:
    if not raw:
        return ""
    value = raw.strip()
    if value.lower().startswith("whatsapp:"):
        value = value.split(":", 1)[1].strip()

    if value.startswith("+"):
        digits = "+" + re.sub(r"\D", "", value)
    else:
        digits_only = re.sub(r"\D", "", value)
        if not digits_only:
            return ""
        if digits_only.startswith("0") and len(digits_only) > 10:
            digits_only = digits_only.lstrip("0")
        if len(digits_only) == 10:
            if DEFAULT_COUNTRY_CODE.startswith("+"):
                digits = DEFAULT_COUNTRY_CODE + digits_only
            else:
                return ""
        elif len(digits_only) > 10:
            digits = "+" + digits_only
        else:
            if DEFAULT_COUNTRY_CODE.startswith("+"):
                digits = DEFAULT_COUNTRY_CODE + digits_only
            else:
                return ""

    numeric = re.sub(r"\D", "", digits)
    if len(numeric) < 8:
        return ""
    return digits


def _looks_like_number(value: str) -> bool:
    return bool(re.search(r"\d{6,}", value or ""))


def _load_twilio_client() -> Optional[Client]:
    global _TWILIO_CLIENT
    if Client is None:
        return None
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        return None
    if _TWILIO_CLIENT is None:
        _TWILIO_CLIENT = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    return _TWILIO_CLIENT


def _twilio_ready() -> bool:
    return _load_twilio_client() is not None and (
        bool(TWILIO_WHATSAPP_FROM) or bool(TWILIO_MESSAGING_SERVICE_SID)
    )


def _send_whatsapp(to_number: str, body: str) -> bool:
    client = _load_twilio_client()
    if client is None:
        return False
    if not TWILIO_WHATSAPP_FROM and not TWILIO_MESSAGING_SERVICE_SID:
        return False

    payload = {
        "to": f"whatsapp:{to_number}",
        "body": body,
    }
    if TWILIO_MESSAGING_SERVICE_SID:
        payload["messaging_service_sid"] = TWILIO_MESSAGING_SERVICE_SID
    else:
        payload["from_"] = TWILIO_WHATSAPP_FROM

    client.messages.create(**payload)
    return True


def _resolve_numbers_for_participants(user_id: int, participants: Iterable[str]) -> Tuple[List[str], List[str]]:
    numbers: Set[str] = set()
    missing: List[str] = []

    with get_connection() as conn:
        for participant in participants:
            name = (participant or "").strip()
            if not name:
                continue

            if _looks_like_number(name):
                normalized = _normalize_number(name)
                if normalized:
                    numbers.add(normalized)
                    continue

            # Exact match first
            rows = conn.execute(
                "SELECT phone_numbers FROM contacts WHERE user_id = ? AND LOWER(name) = LOWER(?)",
                (user_id, name),
            ).fetchall()

            # Fallback: partial match
            if not rows:
                rows = conn.execute(
                    "SELECT phone_numbers FROM contacts WHERE user_id = ? AND LOWER(name) LIKE ?",
                    (user_id, f"%{name.lower()}%"),
                ).fetchall()

            found_any = False
            for row in rows:
                raw_numbers = row[0]
                for candidate in _parse_list(raw_numbers):
                    normalized = _normalize_number(candidate)
                    if normalized:
                        numbers.add(normalized)
                        found_any = True

            if not found_any:
                missing.append(name)

    return sorted(numbers), missing


def _parse_reminder_minutes(reminder_time: Optional[str]) -> Optional[int]:
    if not reminder_time:
        return None
    text = reminder_time.lower()
    match = re.search(r"(\d+)\s*(minute|minutes|min|mins|hour|hours|hr|hrs)", text)
    if not match:
        return None
    amount = int(match.group(1))
    unit = match.group(2)
    if unit.startswith("h"):
        return amount * 60
    return amount


def send_meeting_notifications(
    *,
    user_id: int,
    date: str,
    time: str,
    platform: str,
    meeting_link: str,
    participants: Iterable[str],
    reminder_time: Optional[str],
) -> Dict[str, object]:
    """Send WhatsApp meeting link and schedule reminder."""

    numbers, missing = _resolve_numbers_for_participants(user_id, participants)
    if not numbers:
        return {"sent_count": 0, "missing": missing, "disabled": True}
    if not _twilio_ready():
        return {"sent_count": 0, "missing": missing, "disabled": True}

    intro = f"EchoMeet: Meeting scheduled on {date} at {time} ({platform})."
    body = f"{intro} Join: {meeting_link}"

    sent = 0
    for number in numbers:
        if _send_whatsapp(number, body):
            sent += 1

    reminder_minutes = _parse_reminder_minutes(reminder_time)
    reminder_scheduled = False
    if reminder_minutes:
        try:
            meeting_dt = datetime.fromisoformat(f"{date}T{time}:00")
            reminder_dt = meeting_dt - timedelta(minutes=reminder_minutes)
            delay = (reminder_dt - datetime.now()).total_seconds()
            if delay > 0:
                reminder_body = f"Reminder: Meeting at {time} on {date} ({platform})."
                timer = threading.Timer(delay, _send_bulk, args=(numbers, reminder_body))
                timer.daemon = True
                timer.start()
                _SCHEDULED.append(timer)
                reminder_scheduled = True
        except Exception:
            reminder_scheduled = False

    return {
        "sent_count": sent,
        "missing": missing,
        "reminder_scheduled": reminder_scheduled,
        "disabled": False,
    }


def _send_bulk(numbers: Iterable[str], body: str) -> None:
    for number in numbers:
        try:
            _send_whatsapp(number, body)
        except Exception:
            pass
