from flask import Blueprint, jsonify, request
from app import db
from app.models.user import User

users_bp = Blueprint("users", __name__)

# GET tous les utilisateurs
@users_bp.route("/", methods=["GET"])
def get_users():
    users = User.query.all()
    return jsonify([u.to_dict() for u in users])

# POST créer un utilisateur
@users_bp.route("/", methods=["POST"])
def create_user():
    data = request.get_json()
    user = User(username=data["username"], email=data["email"])
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201