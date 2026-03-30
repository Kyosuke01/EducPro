"""
routes/classes.py — Routes pour les classes et les matières.

Endpoints :
    GET /api/classes                          — Liste de toutes les classes
    GET /api/classes/<class_name>/students    — Étudiants d'une classe
    GET /api/topics                           — Liste de toutes les matières
"""

from flask import Blueprint, jsonify
from app.db import get_db_connection

classes_bp = Blueprint("classes", __name__)


# ──────────────────────────────────────────────
# GET /api/classes
# ──────────────────────────────────────────────
@classes_bp.route("/classes", methods=["GET"])
def get_all_classes():
    """Liste de toutes les classes."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT class_id, name FROM Class ORDER BY name ASC")
            classes = cursor.fetchall()

        return jsonify({"classes": classes}), 200

    except Exception as e:
        return jsonify({"error": f"Erreur serveur : {str(e)}"}), 500
    finally:
        if conn:
            conn.close()


# ──────────────────────────────────────────────
# GET /api/classes/<class_name>/students
# ──────────────────────────────────────────────
@classes_bp.route("/classes/<string:class_name>/students", methods=["GET"])
def get_students_by_class(class_name):
    """Récupère la liste des étudiants inscrits dans une classe spécifique."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = """
                SELECT student_id, first_name, last_name, mail_student, class_name
                FROM Student
                WHERE class_name = %s
                ORDER BY last_name ASC, first_name ASC
            """
            cursor.execute(sql, (class_name,))
            students = cursor.fetchall()

        if students:
            return jsonify({"class_name": class_name, "students": students}), 200
        else:
            return jsonify({"class_name": class_name, "students": []}), 200

    except Exception as e:
        return jsonify({"error": f"Erreur serveur : {str(e)}"}), 500
    finally:
        if conn:
            conn.close()


# ──────────────────────────────────────────────
# GET /api/topics
# ──────────────────────────────────────────────
@classes_bp.route("/topics", methods=["GET"])
def get_all_topics():
    """Récupère la liste de toutes les matières disponibles."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = "SELECT topic_id, name, teacher_id, class_id FROM Topic ORDER BY name ASC"
            cursor.execute(sql)
            topics = cursor.fetchall()

        return jsonify({"topics": topics}), 200

    except Exception as e:
        return jsonify({"error": f"Erreur serveur : {str(e)}"}), 500
    finally:
        if conn:
            conn.close()
