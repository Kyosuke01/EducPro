"""
routes/classes.py — Routes pour les classes et les matières.

Endpoints :
    GET /api/classes                          — Liste de toutes les classes
    GET /api/classes/<class_name>/students    — Étudiants d'une classe
    GET /api/topics                           — Liste de toutes les matières
"""

from flask import Blueprint, jsonify, request
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
            cursor.execute(
                """
                SELECT c.class_id, c.name, c.max_capacity, c.homeroom_teacher_id,
                       COALESCE(t.first_name, '') AS teacher_first_name,
                       COALESCE(t.last_name, '') AS teacher_last_name,
                       COALESCE(t.topic_name, '') AS teacher_topic,
                       COUNT(s.student_id) AS current_size
                FROM Class c
                LEFT JOIN Teacher t ON t.teacher_id = c.homeroom_teacher_id
                LEFT JOIN Student s ON s.class_name = c.name
                GROUP BY c.class_id
                ORDER BY c.name ASC
                """
            )
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
            cursor.execute(
                """
                SELECT c.class_id, c.name, c.max_capacity, c.homeroom_teacher_id,
                       t.first_name AS teacher_first_name,
                       t.last_name AS teacher_last_name,
                       t.topic_name AS teacher_topic
                FROM Class c
                LEFT JOIN Teacher t ON t.teacher_id = c.homeroom_teacher_id
                WHERE c.name = %s
                """,
                (class_name,)
            )
            class_info = cursor.fetchone()

            sql = """
                SELECT student_id, first_name, last_name, mail_student, class_name
                FROM Student
                WHERE class_name = %s
                ORDER BY last_name ASC, first_name ASC
            """
            cursor.execute(sql, (class_name,))
            students = cursor.fetchall()

        response = {
            "class_name": class_name,
            "students": students,
            "class_info": class_info or {}
        }

        if class_info:
            response["current_size"] = len(students)
        else:
            response["current_size"] = 0

        return jsonify(response), 200

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


@classes_bp.route("/classes/<int:class_id>/assign-teacher", methods=["PUT"])
def assign_teacher(class_id):
    data = request.get_json() or {}
    teacher_id = data.get("teacher_id")

    if not teacher_id:
        return jsonify({"error": "teacher_id requis"}), 400

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT class_id FROM Class WHERE class_id = %s", (class_id,))
            classroom = cursor.fetchone()
            if not classroom:
                return jsonify({"error": "Classe introuvable"}), 404

            cursor.execute("SELECT teacher_id FROM Teacher WHERE teacher_id = %s", (teacher_id,))
            teacher = cursor.fetchone()
            if not teacher:
                return jsonify({"error": "Professeur introuvable"}), 404

            cursor.execute(
                "UPDATE Class SET homeroom_teacher_id = %s WHERE class_id = %s",
                (teacher_id, class_id)
            )
            conn.commit()

        return jsonify({"message": "Professeur assigné à la classe."}), 200
    except Exception as e:
        return jsonify({"error": f"Erreur serveur : {str(e)}"}), 500
    finally:
        if conn:
            conn.close()
