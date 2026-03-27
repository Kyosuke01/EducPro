"""
routes/grades.py — Routes pour la gestion des notes.

Endpoints :
    GET  /api/grades/student/<student_id>   — Notes d'un étudiant
    GET  /api/grades/topic/<topic_name>     — Notes par matière
    POST /api/grades                        — Ajouter une note
"""

from flask import Blueprint, request, jsonify
from app.db import get_db_connection

grades_bp = Blueprint("grades", __name__)


# ──────────────────────────────────────────────
# GET /api/grades/student/<int:student_id>
# ──────────────────────────────────────────────
@grades_bp.route("/grades/student/<int:student_id>", methods=["GET"])
def get_grades_by_student(student_id):
    """
    Récupère toutes les notes d'un étudiant donné.

    Retourne :
        200 — Liste des notes de l'étudiant.
        404 — Aucune note trouvée pour cet étudiant.
        500 — Erreur serveur.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = "SELECT grade_id, grade, student_id, topic_name FROM Grade WHERE student_id = %s"
            cursor.execute(sql, (student_id,))
            grades = cursor.fetchall()

        if grades:
            return jsonify({"student_id": student_id, "grades": grades}), 200
        else:
            return jsonify({"error": f"Aucune note trouvée pour l'étudiant {student_id}."}), 404

    except Exception as e:
        return jsonify({"error": f"Erreur serveur : {str(e)}"}), 500
    finally:
        if conn:
            conn.close()


# ──────────────────────────────────────────────
# GET /api/grades/topic/<string:topic_name>
# ──────────────────────────────────────────────
@grades_bp.route("/grades/topic/<string:topic_name>", methods=["GET"])
def get_grades_by_topic(topic_name):
    """
    Récupère toutes les notes pour une matière spécifique.

    Retourne :
        200 — Liste des notes de la matière.
        404 — Aucune note trouvée pour cette matière.
        500 — Erreur serveur.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = "SELECT grade_id, grade, student_id, topic_name FROM Grade WHERE topic_name = %s"
            cursor.execute(sql, (topic_name,))
            grades = cursor.fetchall()

        if grades:
            return jsonify({"topic_name": topic_name, "grades": grades}), 200
        else:
            return jsonify({"error": f"Aucune note trouvée pour la matière '{topic_name}'."}), 404

    except Exception as e:
        return jsonify({"error": f"Erreur serveur : {str(e)}"}), 500
    finally:
        if conn:
            conn.close()


# ──────────────────────────────────────────────
# POST /api/grades
# ──────────────────────────────────────────────
@grades_bp.route("/grades", methods=["POST"])
def create_grade():
    """
    Ajoute une nouvelle note pour un étudiant.

    Body JSON attendu :
        {
            "grade": 15.5,
            "student_id": 1,
            "topic_name": "Mathématiques"
        }

    Retourne :
        201 — Note ajoutée avec succès.
        400 — Champs manquants.
        500 — Erreur serveur.
    """
    data = request.get_json()

    # --- Validation des champs requis ---
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
