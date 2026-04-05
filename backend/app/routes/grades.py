"""
routes/grades.py — Routes pour la gestion des notes.

Endpoints :
    GET  /api/grades/student/<student_id>   — Notes d'un étudiant
    GET  /api/grades/topic/<topic_name>     — Notes par matière
    GET  /api/grades/class/<class_name>     — Notes de tous les étudiants d'une classe
    POST /api/grades                        — Ajouter une note
"""

from flask import Blueprint, request, jsonify
from app.db import get_db_connection
from app.rbac import require_role, check_idor_access

grades_bp = Blueprint("grades", __name__)

# GET /api/grades/student/<int:student_id>


@grades_bp.route("/grades/student/<int:student_id>", methods=["GET"])
def get_grades_by_student(student_id):
    """
    Récupère toutes les notes d'un étudiant donné.
    SECURITY: Vérification IDOR - Un étudiant ne peut voir que ses propres notes
    """
    # SECURITY: Vérifier que l'utilisateur ne contourne pas IDOR
    is_allowed, idor_response = check_idor_access(
        student_id,
        error_message="Vous ne pouvez voir que vos propres notes"
    )
    if not is_allowed:
        return idor_response

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = "SELECT grade_id, grade, student_id, topic_name FROM Grade WHERE student_id = %s"
            cursor.execute(sql, (student_id,))
            grades = cursor.fetchall()

        return jsonify({"student_id": student_id, "grades": grades}), 200

    except Exception as e:
        return jsonify({"error": f"Erreur serveur : {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

# GET /api/grades/topic/<string:topic_name>


@grades_bp.route("/grades/topic/<string:topic_name>", methods=["GET"])
@require_role('teacher', 'admin')
def get_grades_by_topic(topic_name):
    """Récupère toutes les notes pour une matière spécifique (teacher/admin seulement)."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = "SELECT grade_id, grade, student_id, topic_name FROM Grade WHERE topic_name = %s"
            cursor.execute(sql, (topic_name,))
            grades = cursor.fetchall()

        return jsonify({"topic_name": topic_name, "grades": grades}), 200

    except Exception as e:
        return jsonify({"error": f"Erreur serveur : {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

# GET /api/grades/class/<string:class_name>


@grades_bp.route("/grades/class/<string:class_name>", methods=["GET"])
@require_role('teacher', 'admin')
def get_grades_by_class(class_name):
    """Récupère toutes les notes des étudiants d'une classe (teacher/admin seulement)."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = """
                SELECT g.grade_id, g.grade, g.student_id, g.topic_name,
                       s.first_name, s.last_name
                FROM Grade g
                JOIN Student s ON g.student_id = s.student_id
                WHERE s.class_name = %s
                ORDER BY s.last_name, s.first_name, g.topic_name
            """
            cursor.execute(sql, (class_name,))
            grades = cursor.fetchall()

        return jsonify({"class_name": class_name, "grades": grades}), 200

    except Exception as e:
        return jsonify({"error": f"Erreur serveur : {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

# POST /api/grades


@grades_bp.route("/grades", methods=["POST"])
@require_role('admin', 'teacher')
def create_grade():
    """Ajoute une nouvelle note pour un étudiant."""
    data = request.get_json()

    required_fields = ["grade", "student_id", "topic_name"]
    missing = [f for f in required_fields if not data or data.get(f) is None]
    if missing:
        return jsonify({"error": f"Champs manquants : {', '.join(missing)}"}), 400

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = "INSERT INTO Grade (grade, student_id, topic_name) VALUES (%s, %s, %s)"
            cursor.execute(sql, (data["grade"], data["student_id"], data["topic_name"]))
        conn.commit()

        return jsonify({"message": "Note ajoutée avec succès."}), 201

    except Exception as e:
        return jsonify({"error": f"Erreur serveur : {str(e)}"}), 500
    finally:
        if conn:
            conn.close()
