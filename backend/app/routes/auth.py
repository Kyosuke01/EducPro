"""
routes/auth.py — Routes d'authentification et de profils (étudiants/professeurs).

Endpoints :
    POST /api/auth/login              — Connexion d'un étudiant
    GET  /api/students/<int:id>       — Infos d'un étudiant
    GET  /api/teachers/<int:id>       — Infos d'un professeur
"""

from flask import Blueprint, request, jsonify
from app.db import get_db_connection

auth_bp = Blueprint("auth", __name__)


# ──────────────────────────────────────────────
# POST /api/auth/login
# ──────────────────────────────────────────────
@auth_bp.route("/auth/login", methods=["POST"])
def login():
    """
    Authentifie un étudiant à partir de son email et mot de passe.

    Body JSON attendu :
        { "mail_student": "...", "password": "..." }

    Retourne :
        200 — Succès avec les informations de l'étudiant.
        401 — Identifiants invalides.
        400 — Champs manquants.
        500 — Erreur serveur.
    """
    data = request.get_json()

    # --- Validation des champs requis ---
    if not data or not data.get("mail_student") or not data.get("password"):
        return jsonify({"error": "Les champs 'mail_student' et 'password' sont requis."}), 400

    mail = data["mail_student"]
    password = data["password"]

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = "SELECT * FROM Student WHERE mail_student = %s AND password = %s"
            cursor.execute(sql, (mail, password))
            student = cursor.fetchone()

        if student:
            return jsonify({
                "message": "Connexion réussie.",
                "student": student
            }), 200
        else:
            return jsonify({"error": "Email ou mot de passe incorrect."}), 401

    except Exception as e:
        return jsonify({"error": f"Erreur serveur : {str(e)}"}), 500
    finally:
        if conn:
            conn.close()


# ──────────────────────────────────────────────
# GET /api/students/<int:id>
# ──────────────────────────────────────────────
@auth_bp.route("/students/<int:id>", methods=["GET"])
def get_student(id):
    """
    Récupère les informations d'un étudiant par son identifiant.

    Retourne :
        200 — Informations de l'étudiant.
        404 — Étudiant non trouvé.
        500 — Erreur serveur.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = "SELECT student_id, first_name, last_name, mail_student, class_name FROM Student WHERE student_id = %s"
            cursor.execute(sql, (id,))
            student = cursor.fetchone()

        if student:
            return jsonify(student), 200
        else:
            return jsonify({"error": "Étudiant non trouvé."}), 404

    except Exception as e:
        return jsonify({"error": f"Erreur serveur : {str(e)}"}), 500
    finally:
        if conn:
            conn.close()


# ──────────────────────────────────────────────
# GET /api/teachers/<int:id>
# ──────────────────────────────────────────────
@auth_bp.route("/teachers/<int:id>", methods=["GET"])
def get_teacher(id):
    """
    Récupère les informations d'un professeur par son identifiant.

    Retourne :
        200 — Informations du professeur.
        404 — Professeur non trouvé.
        500 — Erreur serveur.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = "SELECT * FROM Teacher WHERE teacher_id = %s"
            cursor.execute(sql, (id,))
            teacher = cursor.fetchone()

        if teacher:
            return jsonify(teacher), 200
        else:
            return jsonify({"error": "Professeur non trouvé."}), 404

    except Exception as e:
        return jsonify({"error": f"Erreur serveur : {str(e)}"}), 500
    finally:
        if conn:
            conn.close()
