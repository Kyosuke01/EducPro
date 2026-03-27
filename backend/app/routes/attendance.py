"""
routes/attendance.py — Routes pour la gestion des absences et retards.

Endpoints :
    GET  /api/attendance/student/<student_id>   — Absences/retards d'un étudiant
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
    """
    Récupère les retards et absences d'un étudiant donné.

    Retourne :
        200 — Liste des entrées d'assiduité de l'étudiant.
        404 — Aucune donnée d'assiduité trouvée.
        500 — Erreur serveur.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = "SELECT attendance_id, late, absent, student_id FROM Attendance WHERE student_id = %s"
            cursor.execute(sql, (student_id,))
            attendance = cursor.fetchall()

        if attendance:
            return jsonify({"student_id": student_id, "attendance": attendance}), 200
        else:
            return jsonify({"error": f"Aucune donnée d'assiduité trouvée pour l'étudiant {student_id}."}), 404

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
    """
    Ajoute ou met à jour une entrée d'assiduité pour un étudiant.

    Si une entrée existe déjà pour le student_id, les compteurs
    de retards et d'absences sont incrémentés.
    Sinon, une nouvelle entrée est créée.

    Body JSON attendu :
        {
            "student_id": 1,
            "late": 1,      (0 ou 1 — ajouter un retard)
            "absent": 0     (0 ou 1 — ajouter une absence)
        }

    Retourne :
        200 — Mise à jour réussie.
        201 — Nouvelle entrée créée.
        400 — Champs manquants.
        500 — Erreur serveur.
    """
    data = request.get_json()

    # --- Validation des champs requis ---
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
            # Vérifier si une entrée existe déjà pour cet étudiant
            cursor.execute("SELECT * FROM Attendance WHERE student_id = %s", (student_id,))
            existing = cursor.fetchone()

            if existing:
                # Mettre à jour : incrémenter les compteurs
                sql = """
                    UPDATE Attendance
                    SET late = late + %s, absent = absent + %s
                    WHERE student_id = %s
                """
                cursor.execute(sql, (late, absent, student_id))
                conn.commit()
                return jsonify({"message": "Assiduité mise à jour avec succès."}), 200
            else:
                # Créer une nouvelle entrée
                sql = "INSERT INTO Attendance (late, absent, student_id) VALUES (%s, %s, %s)"
                cursor.execute(sql, (late, absent, student_id))
                conn.commit()
                return jsonify({"message": "Entrée d'assiduité créée avec succès."}), 201

    except Exception as e:
        return jsonify({"error": f"Erreur serveur : {str(e)}"}), 500
    finally:
        if conn:
            conn.close()
