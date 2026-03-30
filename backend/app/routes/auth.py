"""
routes/auth.py — Routes d'authentification et de profils (étudiants/professeurs).

Endpoints :
    POST /api/auth/login              — Connexion unifiée (étudiant ou professeur/admin)
    GET  /api/students                — Liste de tous les étudiants
    GET  /api/students/<int:id>       — Infos d'un étudiant
    GET  /api/teachers                — Liste de tous les professeurs
    GET  /api/teachers/<int:id>       — Infos d'un professeur
"""

from flask import Blueprint, request, jsonify
from app.db import get_db_connection
import bcrypt

auth_bp = Blueprint("auth", __name__)


# ──────────────────────────────────────────────
# POST /api/auth/login
# ──────────────────────────────────────────────
@auth_bp.route("/auth/login", methods=["POST"])
def login():
    """
    Authentification unifiée : cherche d'abord dans Student, puis Teacher.

    Body JSON attendu :
        { "email": "...", "password": "..." }

    Retourne :
        200 — Succès avec les infos utilisateur et le rôle.
        401 — Identifiants invalides.
        400 — Champs manquants.
        500 — Erreur serveur.
    """
    data = request.get_json()

    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"error": "Les champs 'email' et 'password' sont requis."}), 400

    email = data["email"]
    password = data["password"]

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 1) Chercher dans Student
            cursor.execute(
                "SELECT student_id, first_name, last_name, mail_student, class_name, password "
                "FROM Student WHERE mail_student = %s",
                (email,)
            )
            student = cursor.fetchone()

            if student and bcrypt.checkpw(password.encode('utf-8'), student["password"].encode('utf-8')):
                if request.headers.get("User-Agent") == "educpro-admin/1.0":
                    return jsonify({"error": "Accès refusé. Les étudiants doivent utiliser l'interface normale."}), 403
                return jsonify({
                    "message": "Connexion réussie.",
                    "user": {
                        "id": student["student_id"],
                        "first_name": student["first_name"],
                        "last_name": student["last_name"],
                        "email": student["mail_student"],
                        "class_name": student.get("class_name"),
                        "role": "student"
                    }
                }), 200

            # 2) Chercher dans Teacher
            cursor.execute(
                "SELECT teacher_id, first_name, last_name, mail_teacher, is_admin, topic_name, password "
                "FROM Teacher WHERE mail_teacher = %s",
                (email,)
            )
            teacher = cursor.fetchone()

            if teacher and bcrypt.checkpw(password.encode('utf-8'), teacher["password"].encode('utf-8')):
                role = "admin" if teacher.get("is_admin") else "teacher"
                user_agent = request.headers.get("User-Agent")
                
                if role == "admin" and user_agent != "educpro-admin/1.0":
                    return jsonify({"error": "Accès refusé. Les administrateurs doivent se connecter sur l'interface d'administration."}), 403
                if role == "teacher" and user_agent == "educpro-admin/1.0":
                    return jsonify({"error": "Accès refusé. Les professeurs doivent se connecter sur l'interface normale."}), 403

                return jsonify({
                    "message": "Connexion réussie.",
                    "user": {
                        "id": teacher["teacher_id"],
                        "first_name": teacher["first_name"],
                        "last_name": teacher["last_name"],
                        "email": teacher["mail_teacher"],
                        "topic_name": teacher.get("topic_name"),
                        "role": role
                    }
                }), 200

            # Aucun match ou mauvais mot de passe
            return jsonify({"error": "Email ou mot de passe incorrect."}), 401

    except Exception as e:
        return jsonify({"error": f"Erreur serveur : {str(e)}"}), 500
    finally:
        if conn:
            conn.close()


# ──────────────────────────────────────────────
# GET /api/students
# ──────────────────────────────────────────────
@auth_bp.route("/students", methods=["GET"])
def get_all_students():
    """Liste de tous les étudiants."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT student_id, first_name, last_name, mail_student, class_name, dob "
                "FROM Student ORDER BY last_name, first_name"
            )
            students = cursor.fetchall()

        # Convertir les dates
        for s in students:
            if s.get("dob"):
                s["dob"] = s["dob"].strftime("%Y-%m-%d")

        return jsonify({"students": students}), 200

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
    """Récupère les informations d'un étudiant par son identifiant."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT student_id, first_name, last_name, mail_student, class_name "
                "FROM Student WHERE student_id = %s",
                (id,)
            )
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
# GET /api/teachers
# ──────────────────────────────────────────────
@auth_bp.route("/teachers", methods=["GET"])
def get_all_teachers():
    """Liste de tous les professeurs."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT teacher_id, first_name, last_name, mail_teacher, topic_name, is_admin "
                "FROM Teacher ORDER BY last_name, first_name"
            )
            teachers = cursor.fetchall()

        return jsonify({"teachers": teachers}), 200

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
    """Récupère les informations d'un professeur par son identifiant."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT teacher_id, first_name, last_name, mail_teacher, topic_name, is_admin "
                "FROM Teacher WHERE teacher_id = %s",
                (id,)
            )
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
