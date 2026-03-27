"""
routes/classes.py — Routes pour les classes et les matières.

Endpoints :
    GET /api/classes/<class_name>/students   — Étudiants d'une classe
    GET /api/topics                          — Liste de toutes les matières
"""

from flask import Blueprint, jsonify
from app.db import get_db_connection

classes_bp = Blueprint("classes", __name__)


# ──────────────────────────────────────────────
# GET /api/classes/<class_name>/students
# ──────────────────────────────────────────────
@classes_bp.route("/classes/<string:class_name>/students", methods=["GET"])
def get_students_by_class(class_name):
    """
    Récupère la liste des étudiants inscrits dans une classe spécifique.

    Retourne :
        200 — Liste des étudiants de la classe.
        404 — Aucun étudiant trouvé pour cette classe.
        500 — Erreur serveur.
    """
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
            return jsonify({"error": f"Aucun étudiant trouvé pour la classe '{class_name}'."}), 404

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
    """
    Récupère la liste de toutes les matières disponibles.

    Retourne :
        200 — Liste des matières.
        404 — Aucune matière trouvée.
        500 — Erreur serveur.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = "SELECT topic_id, name, teacher_id, class_id FROM Topic ORDER BY name ASC"
            cursor.execute(sql)
            topics = cursor.fetchall()

        if topics:
            return jsonify({"topics": topics}), 200
        else:
            return jsonify({"error": "Aucune matière trouvée."}), 404

    except Exception as e:
        return jsonify({"error": f"Erreur serveur : {str(e)}"}), 500
    finally:
        if conn:
            conn.close()
