from flask import Blueprint, jsonify
from decorators import token_required, role_required

protected_bp = Blueprint("protected", __name__)

@protected_bp.route("/profile", methods=["GET"])
@token_required
def profile(current_user):
    return jsonify({
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email
    })


@protected_bp.route("/admin", methods=["GET"])
@token_required
@role_required("admin")
def admin_panel(current_user):
    return jsonify({"message": "Welcome Admin"})
