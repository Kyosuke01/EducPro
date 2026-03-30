"""
routes/attendance.py — Routes pour la gestion des absences et retards.

Endpoints :
    GET  /api/attendance/student/<student_id>   — Absences/retards d'un étudiant
    GET  /api/attendance/class/<class_name>     — Absences/retards d'une classe entière
    POST /api/attendance                        — Ajouter ou mettre à jour une absence/retard
"""

from flask import Blueprint, request, jsonify
from app.db import get_db_connection

attendance_bp = Blueprint("attendance", __name__)


# ──────────────────────────────────────────────
# GET /api/attendance/student/<int:student_id>
# ──────────────────────────────────────────────
@attendance_bp.route("/attendance/student/<int:student_id>", methods=["GET"])
def get_attendance_by_student(student_id):
    """Récupère les retards et absences d'un étudiant donné."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = "SELECT attendance_id, late, absent, student_id FROM Attendance WHERE student_id = %s"
            cursor.execute(sql, (student_id,))
            attendance = cursor.fetchall()

        return jsonify({"student_id": student_id, "attendance": attendance}), 200

    except Exception as e:
        return jsonify({"error": f"Erreur serveur : {str(e)}"}), 500
    finally:
        if conn:
            conn.close()


# ──────────────────────────────────────────────
# GET /api/attendance/class/<string:class_name>
# ──────────────────────────────────────────────
@attendance_bp.route("/attendance/class/<string:class_name>", methods=["GET"])
def get_attendance_by_class(class_name):
    """Récupère les absences/retards de tous les étudiants d'une classe."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = """
                SELECT a.attendance_id, a.late, a.absent, a.student_id,
                       s.first_name, s.last_name
                FROM Attendance a
                JOIN Student s ON a.student_id = s.student_id
                WHERE s.class_name = %s
                ORDER BY s.last_name, s.first_name
            """
            cursor.execute(sql, (class_name,))
            attendance = cursor.fetchall()

        return jsonify({"class_name": class_name, "attendance": attendance}), 200

    except Exception as e:
        return jsonify({"error": f"Erreur serveur : {str(e)}"}), 500
    finally:
        if conn:
            conn.close()


# ──────────────────────────────────────────────
# POST /api/attendance
# ──────────────────────────────────────────────
@attendance_bp.route("/attendance", methods=["POST"])
def create_or_update_attendance():
    """Ajoute ou met à jour une entrée d'assiduité pour un étudiant."""
    data = request.get_json()

    required_fields = ["student_id", "late", "absent"]
    missing = [f for f in required_fields if not data or data.get(f) is None]
    if missing:
        return jsonify({"error": f"Champs manquants : {', '.join(missing)}"}), 400

    student_id = data["student_id"]
    late = data["late"]
    absent = data["absent"]

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM Attendance WHERE student_id = %s", (student_id,))
            existing = cursor.fetchone()

            if existing:
                sql = """
                    UPDATE Attendance
                    SET late = late + %s, absent = absent + %s
                    WHERE student_id = %s
                """
                cursor.execute(sql, (late, absent, student_id))
                conn.commit()
                return jsonify({"message": "Assiduité mise à jour avec succès."}), 200
            else:
                sql = "INSERT INTO Attendance (late, absent, student_id) VALUES (%s, %s, %s)"
                cursor.execute(sql, (late, absent, student_id))
                conn.commit()
                return jsonify({"message": "Entrée d'assiduité créée avec succès."}), 201

    except Exception as e:
        return jsonify({"error": f"Erreur serveur : {str(e)}"}), 500
    finally:
        if conn:
            conn.close()
