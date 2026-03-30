from flask import Blueprint, jsonify, request
from app.db import get_db_connection

users_bp = Blueprint("users", __name__)

# GET tous les utilisateurs (Étudiants + Professeurs)
@users_bp.route("/", methods=["GET"])
def get_users():
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Récupérer les étudiants
            cursor.execute("SELECT first_name, last_name, mail_student as email, 'student' as role FROM Student")
            students = cursor.fetchall()
            
            # Récupérer les professeurs
            cursor.execute("SELECT first_name, last_name, mail_teacher as email, 'teacher' as role FROM Teacher")
            teachers = cursor.fetchall()
            
            # Fusionner
            users = []
            for s in students:
                users.append({"username": f"{s['first_name']} {s['last_name']}", "email": s['email'], "role": s['role']})
            for t in teachers:
                users.append({"username": f"{t['first_name']} {t['last_name']}", "email": t['email'], "role": t['role']})
                
        return jsonify(users), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

# POST créer un utilisateur (Exemple simplifié pour compatibilité)
@users_bp.route("/", methods=["POST"])
def create_user():
    return jsonify({"error": "Utilisez les routes spécifiques /api/students ou /api/teachers pour la création"}), 400