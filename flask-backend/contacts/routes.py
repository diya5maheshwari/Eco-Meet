from flask import Blueprint, request, jsonify
from database import get_connection
import json
from datetime import datetime
from decorators import token_required

contacts_bp = Blueprint('contacts', __name__)

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
                phone_numbers = json.dumps(contact.get('phoneNumbers', []))
                emails = json.dumps(contact.get('emails', []))
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
