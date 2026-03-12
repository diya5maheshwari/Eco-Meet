"""Custom Rasa actions and validators for meeting scheduling."""

import re
from datetime import datetime
from typing import Any, Dict, List, Text

import dateparser
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormValidationAction
from rasa_sdk.types import DomainDict
from dateparser.search import search_dates


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
TIME_RE = re.compile(
    r"\b((1[0-2]|0?[1-9])(:[0-5][0-9])?\s*[AaPp][Mm]|([01]?[0-9]|2[0-3]):[0-5][0-9]|noon|midnight|morning|afternoon|evening|night)\b"
)
DOT_TIME_RE = re.compile(r"\b(\d{1,2})\.(\d{2})\b")
SPACE_TIME_RE = re.compile(r"\b(\d{1,2})\s+(\d{2})\s*([AaPp][Mm])?\b")


def _normalize_time_text(text: Text) -> Text:
    """Normalize common time formats like 6.18 or '6 18 AM' to 6:18 AM."""
    if not text:
        return text
    updated = DOT_TIME_RE.sub(r"\1:\2", text)

    def _space_repl(match: re.Match) -> str:
        hour, minute, ampm = match.group(1), match.group(2), match.group(3) or ""
        start = match.start()
        prefix = updated[max(0, start - 6):start].lower()
        if "at" in prefix or ampm:
            return f"{hour}:{minute} {ampm}".strip()
        return match.group(0)

    return SPACE_TIME_RE.sub(_space_repl, updated)
PARTICIPANT_HINT_RE = re.compile(
    r"(?:with|for|invite|including|add)\s+(.+?)(?:\s+(?:on|at|by|via|using|tomorrow|today|next|this)\b|$)",
    re.IGNORECASE,
)


def _normalize_platform(value: Text) -> Text:
    """Map platform aliases from free text to canonical platform names."""
    key = re.sub(r"\s+", " ", value.strip().lower())
    return PLATFORM_ALIASES.get(key, value.strip())


def _split_participants(value: Any) -> List[Text]:
    """Split a participant string/list into individual candidate names."""
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
    """Collect entity values of a given type from latest user message."""
    entities = tracker.latest_message.get("entities", []) or []
    values = []
    for ent in entities:
        if ent.get("entity") == entity_type and isinstance(ent.get("value"), str):
            values.append(ent["value"])
    return values


def _is_valid_name(name: Text) -> bool:
    """Validate participant tokens and reject obvious non-person terms."""
    lower = name.strip().lower()
    if lower in INVALID_NAME_TOKENS:
        return False
    if re.search(r"\d", lower):
        return False
    return bool(NAME_RE.match(name.strip()))


def _latest_text(tracker: Tracker) -> Text:
    """Return latest user message text (or empty string)."""
    return (tracker.latest_message.get("text") or "").strip()


def _extract_platform_from_text(text: Text) -> Text:
    """Extract a known platform from unstructured user text."""
    lowered = f" {text.lower()} "
    for alias, canonical in PLATFORM_ALIASES.items():
        if f" {alias} " in lowered:
            return canonical
    return ""


def _extract_date_from_text(text: Text) -> Text:
    """Extract a future date from user text as ISO yyyy-mm-dd."""
    if not text:
        return ""
    matches = search_dates(
        text,
        settings={"PREFER_DATES_FROM": "future", "RELATIVE_BASE": datetime.now()},
        languages=["en"],
    ) or []
    now = datetime.now()
    for _, dt in matches:
        if dt.date() >= now.date():
            return dt.date().isoformat()
    return ""


def _extract_time_from_text(text: Text) -> Text:
    """Extract a time from user text as HH:MM (24-hour)."""
    if not text:
        return ""
    text = _normalize_time_text(text)
    match = TIME_RE.search(text)
    candidate = match.group(1) if match else text
    parsed = dateparser.parse(candidate)
    if not parsed:
        return ""
    return parsed.strftime("%H:%M")


def _extract_reminder_from_text(text: Text) -> Text:
    """Extract reminder duration and normalize to 'X minutes before'."""
    match = re.search(
        r"(?:remind(?: me)?\s*)?(\d+)\s*(minute|minutes|min|mins|hour|hours|hr|hrs)\s*(?:before|earlier)?",
        text.lower(),
    )
    if not match:
        return ""
    amount = int(match.group(1))
    unit = match.group(2)
    minutes = amount * 60 if unit.startswith("h") else amount
    return f"{minutes} minutes before"


def _extract_participants_from_text(text: Text) -> List[Text]:
    """Extract participant names from common phrasing patterns."""
    if not text:
        return []
    chunks = []
    for m in PARTICIPANT_HINT_RE.finditer(text):
        chunks.append(m.group(1))
    if not chunks:
        return []

    raw = ", ".join(chunks)
    names = _split_participants(raw)
    valid = [n.title() for n in names if _is_valid_name(n)]
    return list(dict.fromkeys(valid))


class ValidateScheduleMeetingForm(FormValidationAction):
    """Form validator/extractor for meeting slots."""

    def name(self) -> Text:
        """Return action name configured in domain."""
        return "validate_schedule_meeting_form"

    def validate_participants(
        self,
        value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate participant slot and enforce name quality checks."""
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

    def extract_participants(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Attempt participant extraction even when entity extraction misses."""
        entity_names = []
        entity_names += _entities_by_type(tracker, "participants")
        entity_names += _entities_by_type(tracker, "participant")
        entity_names += _entities_by_type(tracker, "person")
        names = _split_participants(entity_names) if entity_names else _extract_participants_from_text(_latest_text(tracker))
        valid = [n.title() for n in names if _is_valid_name(n)]
        valid = list(dict.fromkeys(valid))
        return {"participants": valid} if valid else {}

    def validate_date(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate and normalize date slot."""
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

    def extract_date(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Attempt date extraction from latest message text."""
        text = _latest_text(tracker)
        extracted = _extract_date_from_text(text)
        return {"date": extracted} if extracted else {}

    def validate_time(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate and normalize time slot."""
        normalized = _normalize_time_text(value) if isinstance(value, str) else value
        parsed = dateparser.parse(normalized)
        if not parsed:
            dispatcher.utter_message(response="utter_invalid_time")
            return {"time": None}

        return {"time": parsed.strftime("%H:%M")}

    def extract_time(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Attempt time extraction from latest message text."""
        text = _latest_text(tracker)
        extracted = _extract_time_from_text(text)
        return {"time": extracted} if extracted else {}

    def validate_platform(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate platform slot, defaulting to Google Meet when absent."""
        normalized = _normalize_platform(value)
        if not normalized:
            return {"platform": "Google Meet"}
        if normalized not in PLATFORM_ALIASES.values():
            dispatcher.utter_message(response="utter_invalid_platform")
            return {"platform": None}
        return {"platform": normalized}

    def extract_platform(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Attempt platform extraction from entities or latest text."""
        entities = _entities_by_type(tracker, "platform")
        if entities:
            normalized = _normalize_platform(entities[0])
            if normalized:
                return {"platform": normalized}
        text = _latest_text(tracker)
        extracted = _extract_platform_from_text(text)
        return {"platform": extracted} if extracted else {}

    def validate_reminder_time(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate reminder slot."""
        normalized = _extract_reminder_from_text(value)
        if not normalized:
            dispatcher.utter_message(response="utter_invalid_reminder")
            return {"reminder_time": None}
        return {"reminder_time": normalized}

    def extract_reminder_time(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Attempt reminder extraction from entities or latest text."""
        entities = _entities_by_type(tracker, "reminder_time")
        if entities:
            normalized = _extract_reminder_from_text(entities[0])
            if normalized:
                return {"reminder_time": normalized}
        text = _latest_text(tracker)
        extracted = _extract_reminder_from_text(text)
        return {"reminder_time": extracted} if extracted else {}


class ActionSubmitMeeting(Action):
    """Emit final meeting payload after form completion."""

    def name(self) -> Text:
        """Return action name configured in domain."""
        return "action_submit_meeting"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[Dict[Text, Any]]:
        """Build and send final structured payload + human-readable confirmation."""
        platform = tracker.get_slot("platform") or "Google Meet"
        participants = tracker.get_slot("participants") or []
        payload = {
            "type": "meeting_data",
            "date": tracker.get_slot("date"),
            "time": tracker.get_slot("time"),
            "platform": platform,
            "participants": participants,
            "reminder_time": tracker.get_slot("reminder_time"),
            "user_id": tracker.sender_id,
        }

        if not tracker.get_slot("platform"):
            dispatcher.utter_message(
                text="Platform not provided, choosing Google Meet as the default platform. You can change it anytime."
            )

        dispatcher.utter_message(
            text=(
                f"Meeting details captured: date {payload['date']}, time {payload['time']}, "
                f"platform {payload['platform']}, participants {', '.join(participants) if participants else 'None'}, "
                f"reminder {payload['reminder_time']}."
            )
        )
        dispatcher.utter_message(json_message=payload)

        return []
