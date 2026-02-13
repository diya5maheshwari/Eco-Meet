"""Authentication endpoints for register/login/logout."""

from flask import Blueprint, request, jsonify, make_response
import bcrypt
import jwt
import sqlite3
from datetime import datetime, timedelta
from config import SECRET_KEY
from database import get_connection

auth_bp = Blueprint("auth", __name__)


def _json_body():
    """Safely read a JSON object body; return None for invalid/non-object payloads."""
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None


@auth_bp.route("/register", methods=["POST"])
def register():
    """Create a new user account with hashed password."""
    data = _json_body()
    if data is None:
        return jsonify({"message": "Invalid JSON body"}), 400

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not name or not email or not password:
        return jsonify({"message": "Missing fields"}), 400

    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    try:
        with get_connection() as conn:
            conn.execute("""
                INSERT INTO users (name, email, password, created_at)
                VALUES (?, ?, ?, ?)
            """, (name, email, hashed_pw.decode(), datetime.utcnow().isoformat()))

        return jsonify({"message": "Registered successfully"}), 201

    except sqlite3.IntegrityError:
        return jsonify({"message": "User already exists"}), 400
    except Exception:
        return jsonify({"message": "Failed to register user"}), 500


@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate user credentials and return a signed JWT token."""
    data = _json_body()
    if data is None:
        return jsonify({"message": "Invalid JSON body"}), 400

    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"message": "Missing email or password"}), 400

    with get_connection() as conn:
        user = conn.execute(
            "SELECT id, name, email, password, role FROM users WHERE email = ?",
            (email,)
        ).fetchone()

    if not user:
        return jsonify({"message": "Invalid credentials"}), 401

    if not bcrypt.checkpw(password.encode(), user[3].encode()):
        return jsonify({"message": "Invalid credentials"}), 401

    token = jwt.encode(
        {
            "id": user[0],
            "role": user[4],
            "exp": datetime.utcnow() + timedelta(days=1)
        },
        SECRET_KEY,
        algorithm="HS256"
    )

    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": {
            "id": user[0],
            "name": user[1],
            "email": user[2],
            "role": user[4]
        }
    })


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """Clear cookie token (for clients that still rely on cookie-based auth)."""
    response = make_response(jsonify({"message": "Logged out"}))
    response.set_cookie("token", "", max_age=0)
    return response
