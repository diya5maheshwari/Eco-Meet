"""Reusable auth/role decorators for Flask routes."""

import jwt
from flask import request, jsonify
from functools import wraps
from flask_backend.config import SECRET_KEY
from flask_backend.database import get_connection


def token_required(f):
    """Require a valid JWT Bearer token and inject current user tuple."""
    @wraps(f)
    def decorated(*args, **kwargs):

        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"message": "Token missing"}), 401

        token = auth_header.split(" ")[1]

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = data["id"]

            with get_connection() as conn:
                user = conn.execute(
                    "SELECT id, name, email, role FROM users WHERE id = ?",
                    (user_id,)
                ).fetchone()

            if not user:
                return jsonify({"message": "User not found"}), 401

        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid token"}), 401

        return f(user, *args, **kwargs)

    return decorated


def role_required(role):
    """Require a specific role value from the authenticated user tuple."""
    def wrapper(f):
        @wraps(f)
        def decorated(current_user, *args, **kwargs):

            if current_user[3] != role:
                return jsonify({"message": "Forbidden"}), 403

            return f(current_user, *args, **kwargs)

        return decorated
    return wrapper
