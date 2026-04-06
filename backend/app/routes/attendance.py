"""
routes/attendance.py — Routes pour la gestion des absences et retards.

Endpoints :
    GET  /api/attendance/stats              — Stats globales d'assiduité (tous les étudiants)
    GET  /api/attendance/student/<student_id>   — Absences/retards d'un étudiant
    GET  /api/attendance/class/<class_name>     — Absences/retards d'une classe entière
    POST /api/attendance                        — Ajouter ou mettre à jour une absence/retard
"""

from flask import Blueprint, request, jsonify
from app.db import get_db_connection
from app.rbac import require_role, check_idor_access

attendance_bp = Blueprint("attendance", __name__)

# GET /api/attendance/stats


@attendance_bp.route("/attendance/stats", methods=["GET"])
def get_attendance_stats():
    """Récupère les statistiques globales d'assiduité (tous les étudiants)."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = """
                SELECT
                    COUNT(*) AS total_events,
                    SUM(CASE WHEN status = 'late' THEN 1 ELSE 0 END) AS late_count,
                    SUM(CASE WHEN status = 'absent' THEN 1 ELSE 0 END) AS absent_count
                FROM ATTENDANCE
            """
            cursor.execute(sql)
            result = cursor.fetchone()

        late_count = result['late_count'] or 0
        absent_count = result['absent_count'] or 0
        total_events = result['total_events'] or 0
        stats = {
            'total': total_events,
            'late': late_count,
            'absent': absent_count,
            'onTime': max(0, total_events - late_count - absent_count)
        }

        return jsonify({"stats": stats}), 200

    except Exception as e:
        return jsonify({"error": f"Erreur serveur : {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

# GET /api/attendance/student/<int:student_id>


@attendance_bp.route("/attendance/student/<int:student_id>", methods=["GET"])
def get_attendance_by_student(student_id):
    """
    Récupère les retards et absences d'un étudiant donné.
    SECURITY: Vérification IDOR - Un étudiant ne peut voir que ses propres absences
    """
    # SECURITY: Vérifier que l'utilisateur ne contourne pas IDOR
    is_allowed, idor_response = check_idor_access(
        student_id,
        error_message="Vous ne pouvez voir que vos propres données d'assiduité"
    )
    if not is_allowed:
        return idor_response

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = """
                SELECT attendance_id, student_id, edt_id, date_attendance, status, justified
                FROM ATTENDANCE
                WHERE student_id = %s
                ORDER BY date_attendance DESC, attendance_id DESC
            """
            cursor.execute(sql, (student_id,))
            attendance = cursor.fetchall()

        return jsonify({"student_id": student_id, "attendance": attendance}), 200

    except Exception as e:
        return jsonify({"error": f"Erreur serveur : {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

# GET /api/attendance/class/<string:class_name>


@attendance_bp.route("/attendance/class/<string:class_name>", methods=["GET"])
def get_attendance_by_class(class_name):
    """Récupère les absences/retards de tous les étudiants d'une classe."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = """
                SELECT a.attendance_id, a.student_id, a.edt_id, a.date_attendance, a.status, a.justified,
                       s.first_name, s.last_name, s.class_name
                FROM ATTENDANCE a
                JOIN Student s ON a.student_id = s.student_id
                WHERE s.class_name = %s
                ORDER BY a.date_attendance DESC, s.last_name, s.first_name
            """
            cursor.execute(sql, (class_name,))
            attendance = cursor.fetchall()

        return jsonify({"class_name": class_name, "attendance": attendance}), 200

    except Exception as e:
        return jsonify({"error": f"Erreur serveur : {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

# POST /api/attendance


@attendance_bp.route("/attendance", methods=["POST"])
@require_role('admin', 'teacher')
def create_or_update_attendance():
    """Ajoute ou met à jour une entrée d'assiduité pour un étudiant."""
    data = request.get_json()

    required_fields = ["student_id", "late", "absent"]
    missing = [f for f in required_fields if not data or data.get(f) is None]
    if missing:
        return jsonify({"error": f"Champs manquants : {', '.join(missing)}"}), 400

    student_id = data["student_id"]
    late = int(data["late"] or 0)
    absent = int(data["absent"] or 0)
    if late < 0 or absent < 0:
        return jsonify({"error": "Les valeurs late/absent doivent être positives."}), 400
    if late == 0 and absent == 0:
        return jsonify({"error": "Aucune action à enregistrer."}), 400

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT e.edt_id
                FROM EDT e
                JOIN Student s ON s.class_name = e.class_name
                WHERE s.student_id = %s
                ORDER BY e.start_time DESC
                LIMIT 1
                """,
                (student_id,)
            )
            edt_row = cursor.fetchone()
            linked_edt_id = edt_row["edt_id"] if edt_row else None
            attendance_date = data.get("date_attendance")

            for _ in range(late):
                cursor.execute(
                    """
                    INSERT INTO ATTENDANCE (student_id, edt_id, date_attendance, status, justified)
                    VALUES (%s, %s, COALESCE(%s, CURDATE()), 'late', 0)
                    """,
                    (student_id, linked_edt_id, attendance_date)
                )

            for _ in range(absent):
                cursor.execute(
                    """
                    INSERT INTO ATTENDANCE (student_id, edt_id, date_attendance, status, justified)
                    VALUES (%s, %s, COALESCE(%s, CURDATE()), 'absent', 0)
                    """,
                    (student_id, linked_edt_id, attendance_date)
                )

        conn.commit()
        return jsonify({"message": "Assiduité enregistrée avec succès."}), 201

    except Exception as e:
        return jsonify({"error": f"Erreur serveur : {str(e)}"}), 500
    finally:
        if conn:
            conn.close()
