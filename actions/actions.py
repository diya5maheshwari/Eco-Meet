"""Custom Rasa actions and validators for meeting scheduling."""

import re
from datetime import datetime
from typing import Any, Dict, List, Text
from rasa_sdk.events import SlotSet
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
PARTICIPANT_HINT_RE = re.compile(
    r"(?:with|for|invite|including|add)\s+(.+?)(?:\s+(?:on|at|by|via|using|tomorrow|today|next|this)\b|$)",
    re.IGNORECASE,
)


def _normalize_platform(value: Text) -> Text:
    """Map platform aliases from free text to canonical platform names."""
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

    cleaned = re.sub(r"[^\w\s,@.'\-]", " ", value)

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
    """Allow either names or email addresses."""

    name = name.strip()

    email_regex = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    if re.match(email_regex, name):
        return True

    lower = name.lower()

    if lower in INVALID_NAME_TOKENS:
        return False

    if re.search(r"\d", lower):
        return False

    return bool(NAME_RE.match(name))

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

    # Only try extracting time if a time pattern exists
    if not TIME_RE.search(text):
        return ""

    match = TIME_RE.search(text)
    candidate = match.group(1) if match else text

    parsed = dateparser.parse(candidate)

    if not parsed:
        return ""

    return parsed.strftime("%H:%M")


def _extract_reminder_from_text(text: Text) -> Text:

    if not text:
        return ""

    text = text.lower()

    # Handle natural phrases
    if "half hour" in text:
        return "30 minutes before"

    if "quarter hour" in text:
        return "15 minutes before"

    # word → number mapping
    word_to_number = {
        "one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7,"eight":8,"nine":9,"ten":10,
        "eleven":11,"twelve":12,"thirteen":13,"fourteen":14,"fifteen":15,"sixteen":16,"seventeen":17,
        "eighteen":18,"nineteen":19,"twenty":20,"thirty":30,"forty":40,"fifty":50,"sixty":60
    }

    match = re.search(
        r"(?:remind(?: me)?\s*)?(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty)\s*(minute|minutes|min|mins|hour|hours|hr|hrs)(?:\s*before)?",
        text,
    )

    if not match:
        return ""

    amount = match.group(1)
    unit = match.group(2)

    # convert words to numbers
    if amount.isdigit():
        amount = int(amount)
    else:
        amount = word_to_number.get(amount, 0)

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
    valid = [
    n if "@" in n else n.title()
    for n in names
    if _is_valid_name(n)
]
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

        entity_names = []
        entity_names += _entities_by_type(tracker, "participants")
        entity_names += _entities_by_type(tracker, "participant")
        entity_names += _entities_by_type(tracker, "person")

        if entity_names:
            names = entity_names
        else:
            names = _split_participants(value)

        valid = [
            n if "@" in n else n.title()
            for n in names
            if _is_valid_name(n)
        ]

        # If any email is present, remove names to avoid duplication
        emails = [n for n in valid if "@" in n]
        if emails:
            valid = emails

        # De-duplicate while preserving order
        filtered = []
        for name in valid:
                if not any(name != other and name.lower() in other.lower() for other in valid):
                    filtered.append(name)

        valid = list(dict.fromkeys(filtered))

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
        valid = [
            n if "@" in n else n.title()
            for n in names
            if _is_valid_name(n)
        ]
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
        parsed = dateparser.parse(value)
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
           return {"platform": None}
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

        normalized = _extract_reminder_from_text(value)

        return {"reminder_time": normalized}


    def extract_reminder_time(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: DomainDict,
        ) -> Dict[Text, Any]:
        """Attempt reminder extraction only if user explicitly mentions reminder."""

        entities = _entities_by_type(tracker, "reminder_time")

        if entities:
            normalized = _extract_reminder_from_text(entities[0])
            if normalized:
                return {"reminder_time": normalized}

        text = _latest_text(tracker).lower()

        # Only extract reminder if user explicitly mentions reminder
        if "remind" not in text:
         return {}

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
                f"Great! I've captured your meeting details.\n"
                f"📅 Date: {payload['date']}\n"
                f"⏰ Time: {payload['time']}\n"
                f"💻 Platform: {payload['platform']}\n"
                f"👥 Participants: {', '.join(participants) if participants else 'None'}\n"
                f"🔔 Reminder: {payload['reminder_time']}"
            )
        )
        dispatcher.utter_message(json_message=payload)

        return [
            SlotSet("date", None),
            SlotSet("time", None),
            SlotSet("platform", None),
            SlotSet("participants", None),
            SlotSet("reminder_time", None)
        ]
    
class ActionRescheduleMeeting(Action):

    def name(self):
        return "action_reschedule_meeting"

    def run(self, dispatcher, tracker, domain):
        participant = next(tracker.get_latest_entity_values("participant"), None)
        if not participant:
         dispatcher.utter_message(text="Which meeting should I modify?")
         return []
        new_time = tracker.get_slot("time")

        from flask_backend.database import get_connection

        with get_connection() as conn:

            row = conn.execute(
                "SELECT id FROM meetings WHERE participants LIKE ? ORDER BY created_at DESC LIMIT 1",
                (f"%{participant}%",)
            ).fetchone()

            if not row:
                dispatcher.utter_message(text="I couldn't find that meeting.")
                return []

            meeting_id = row[0]

            conn.execute(
                "UPDATE meetings SET time=? WHERE id=?",
                (new_time, meeting_id)
            )

        dispatcher.utter_message(
            text=f"Your meeting with {participant} has been moved to {new_time}."
        )

        return []
    
class ActionCancelMeeting(Action):

    def name(self):
        return "action_cancel_meeting"

    def run(self, dispatcher, tracker, domain):

        participant = next(tracker.get_latest_entity_values("participant"), None)

        if not participant:
            dispatcher.utter_message(text="Which meeting should I cancel?")
            return []

        from flask_backend.database import get_connection

        with get_connection() as conn:

            row = conn.execute(
                "SELECT id FROM meetings WHERE participants LIKE ? ORDER BY created_at DESC LIMIT 1",
                (f"%{participant}%",)
            ).fetchone()

            if not row:
                dispatcher.utter_message(text="I couldn't find that meeting.")
                return []

            meeting_id = row[0]

            conn.execute(
                "DELETE FROM meetings WHERE id=?",
                (meeting_id,)
            )

        dispatcher.utter_message(
            text=f"The meeting with {participant} has been cancelled."
        )

        return []
    
class ActionAddParticipant(Action):

    def name(self):
        return "action_add_participant"

    def run(self, dispatcher, tracker, domain):

        new_person = next(tracker.get_latest_entity_values("participant"), None)

        if not new_person:
            dispatcher.utter_message(text="Who should I add to the meeting?")
            return []

        from flask_backend.database import get_connection
        import json

        with get_connection() as conn:

            row = conn.execute(
                "SELECT id, participants FROM meetings ORDER BY created_at DESC LIMIT 1"
            ).fetchone()

            if not row:
                dispatcher.utter_message(text="No meeting found to update.")
                return []

            meeting_id = row[0]
            try:
                participants = json.loads(row[1])
            except:
                participants = [row[1]]

            if new_person not in participants:
              participants.append(new_person)

            conn.execute(
                "UPDATE meetings SET participants=? WHERE id=?",
                (json.dumps(participants), meeting_id)
            )

        dispatcher.utter_message(
            text=f"{new_person} has been added to the meeting."
        )

        return []