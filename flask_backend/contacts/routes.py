from flask import Blueprint, request, jsonify
from flask_backend.database import get_connection
import json
from datetime import datetime
from flask_backend.decorators import token_required

contacts_bp = Blueprint('contacts', __name__)

def _to_list(value):
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


@contacts_bp.route('/sync', methods=['POST'])
@token_required
def sync_contacts(current_user):
    data = request.get_json()
    contacts = data.get('contacts', [])
    user_id = current_user[0]

    if not contacts:
        return jsonify({"message": "No contacts provided"}), 400

    print(f"Syncing {len(contacts)} contacts for user {user_id}")

    try:
        with get_connection() as conn:
            # Optional: Clear old contacts for this user before inserting new ones
            # conn.execute("DELETE FROM contacts WHERE user_id = ?", (user_id,))

            for contact in contacts:
                name = contact.get('name', 'Unknown')
                raw_numbers = contact.get('phoneNumbers', None)
                if raw_numbers is None:
                    raw_numbers = contact.get('phone_numbers', None)
                phone_numbers = json.dumps(_to_list(raw_numbers))

                raw_emails = contact.get('emails', None)
                if raw_emails is None:
                    raw_emails = contact.get('email', None)
                emails = json.dumps(_to_list(raw_emails))

                synced_at = datetime.utcnow().isoformat()

                conn.execute("""
                    INSERT INTO contacts (user_id, name, phone_numbers, emails, synced_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, name, phone_numbers, emails, synced_at))

            conn.commit()

        return jsonify({"message": f"Successfully synced {len(contacts)} contacts"}), 200
    except Exception as e:
        print(f"Error syncing contacts: {e}")
        return jsonify({"error": str(e)}), 500

@contacts_bp.route('/count', methods=['GET'])
@token_required
def get_contact_count(current_user):
    """Return the number of synced contacts for the user."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM contacts WHERE user_id = ?",
            (current_user[0],)
        ).fetchone()
        count = row[0] if row else 0
        
    return jsonify({"count": count})
