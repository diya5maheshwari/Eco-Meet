import json
from flask_backend.database import get_connection

def get_contact_email(user_id, name):

    with get_connection() as conn:
        row = conn.execute(
            "SELECT emails FROM contacts WHERE user_id=? AND LOWER(name)=LOWER(?) LIMIT 1",
            (user_id, name)
        ).fetchone()

    if not row:
        return None

    emails = json.loads(row[0])

    if isinstance(emails, list) and len(emails) > 0:
        return emails[0]

    return None