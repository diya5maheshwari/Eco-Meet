import os
import re
from datetime import datetime
from typing import Any, Dict, List, Text

import requests
import dateparser
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormValidationAction
from rasa_sdk.types import DomainDict


PLATFORM_ALIASES = {
    "zoom": "Zoom",
    "google meet": "Google Meet",
    "googlemeet": "Google Meet",
    "gmeet": "Google Meet",
    "meet": "Google Meet",
    "teams": "Teams",
    "microsoft teams": "Teams",
    "webex": "Webex",
    "skype": "Skype",
    "slack": "Slack Call",
    "slack call": "Slack Call",
}

INVALID_NAME_TOKENS = {
    "me", "myself", "you", "yourself", "him", "her", "them", "everyone", "everybody",
    "all", "anyone", "someone", "nobody", "none", "it", "this", "that", "these", "those",
    "cat", "dog", "animal", "bird", "tree", "rock", "chair", "table", "banana", "apple",
    "mango", "cup", "bottle", "door", "window", "lamp", "fan", "pencil", "pen", "book",
}

NAME_RE = re.compile(r"^[A-Za-z][A-Za-z .'\-]{0,49}$")


def _normalize_platform(value: Text) -> Text:
    key = re.sub(r"\s+", " ", value.strip().lower())
    return PLATFORM_ALIASES.get(key, value.strip())


def _split_participants(value: Any) -> List[Text]:
    if isinstance(value, list):
        raw = []
        for item in value:
            if isinstance(item, str):
                raw.append(item)
        value = ", ".join(raw)

    if not isinstance(value, str):
        return []

    cleaned = re.sub(r"[^\w\s,']", " ", value)
    tokens = re.split(r",\s*|\s+and\s+|\s*&\s*", cleaned.strip())
    return [t.strip() for t in tokens if t.strip()]


def _entities_by_type(tracker: Tracker, entity_type: Text) -> List[Text]:
    entities = tracker.latest_message.get("entities", []) or []
    values = []
    for ent in entities:
        if ent.get("entity") == entity_type and isinstance(ent.get("value"), str):
            values.append(ent["value"])
    return values


def _is_valid_name(name: Text) -> bool:
    lower = name.strip().lower()
    if lower in INVALID_NAME_TOKENS:
        return False
    if re.search(r"\d", lower):
        return False
    return bool(NAME_RE.match(name.strip()))


class ValidateScheduleMeetingForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_schedule_meeting_form"

    def validate_participants(
        self,
        value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        # Prefer explicit participant entities; ignore invalid_participant if valid names exist.
        entity_names = []
        entity_names += _entities_by_type(tracker, "participants")
        entity_names += _entities_by_type(tracker, "participant")
        entity_names += _entities_by_type(tracker, "person")

        names = _split_participants(entity_names or value)
        valid = [n.title() for n in names if _is_valid_name(n)]
        # De-duplicate while preserving order
        valid = list(dict.fromkeys(valid))
        invalid = [n for n in names if not _is_valid_name(n)]

        if not valid:
            dispatcher.utter_message(text="Please provide at least one valid participant name.")
            return {"participants": None, "invalid_participant": invalid}

        if invalid:
            dispatcher.utter_message(
                text=f"I couldn't recognize these as valid participant names: {', '.join(invalid)}. "
                     "Please correct them."
            )
            return {"participants": None, "invalid_participant": invalid}

        return {"participants": valid, "invalid_participant": []}

    def validate_date(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        parsed = dateparser.parse(
            value,
            settings={"PREFER_DATES_FROM": "future", "RELATIVE_BASE": datetime.now()},
        )
        if not parsed:
            dispatcher.utter_message(response="utter_invalid_date")
            return {"date": None}

        today = datetime.now().date()
        if parsed.date() < today:
            dispatcher.utter_message(response="utter_invalid_date")
            return {"date": None}

        return {"date": parsed.date().isoformat()}

    def validate_time(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        parsed = dateparser.parse(value)
        if not parsed:
            dispatcher.utter_message(response="utter_invalid_time")
            return {"time": None}

        return {"time": parsed.strftime("%H:%M")}

    def validate_platform(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        normalized = _normalize_platform(value)
        if normalized not in PLATFORM_ALIASES.values():
            dispatcher.utter_message(response="utter_invalid_platform")
            return {"platform": None}
        return {"platform": normalized}

    def validate_reminder_time(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        match = re.search(r"(\d+)\s*(minute|minutes|min|mins|hour|hours|hr|hrs)", value.lower())
        if not match:
            dispatcher.utter_message(response="utter_invalid_reminder")
            return {"reminder_time": None}

        amount = int(match.group(1))
        unit = match.group(2)
        minutes = amount * 60 if unit.startswith("h") else amount
        return {"reminder_time": f"{minutes} minutes before"}


class ActionSubmitMeeting(Action):
    def name(self) -> Text:
        return "action_submit_meeting"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[Dict[Text, Any]]:
        payload = {
            "date": tracker.get_slot("date"),
            "time": tracker.get_slot("time"),
            "platform": tracker.get_slot("platform"),
            "participants": tracker.get_slot("participants") or [],
            "reminder_time": tracker.get_slot("reminder_time"),
            "user_id": tracker.sender_id,
        }

        dispatcher.utter_message(response="utter_slots_values")

        api_url = os.getenv("SCHEDULER_API_URL")
        if api_url:
            try:
                requests.post(api_url, json=payload, timeout=5)
                dispatcher.utter_message(text="Meeting request sent to the scheduler.")
            except requests.RequestException:
                dispatcher.utter_message(
                    text="I couldn't reach the scheduler right now. Please try again."
                )
        else:
            dispatcher.utter_message(
                text="Scheduler is not configured yet. Set SCHEDULER_API_URL to enable scheduling."
            )

        return []
