"""
routes/edt.py — Routes pour la gestion des emplois du temps (EDT).

Endpoints :
    GET  /api/edt/class/<class_name>        — EDT d'une classe
    GET  /api/edt/teacher/<teacher_l_name>  — EDT d'un professeur
    POST /api/edt                           — Ajouter une entrée EDT
"""

from flask import Blueprint, request, jsonify
from app.db import get_db_connection

edt_bp = Blueprint("edt", __name__)


# ──────────────────────────────────────────────
# GET /api/edt/class/<class_name>
# ──────────────────────────────────────────────
@edt_bp.route("/edt/class/<string:class_name>", methods=["GET"])
def get_edt_by_class(class_name):
    """
    Récupère l'emploi du temps complet d'une classe donnée.

    Retourne :
        200 — Liste des créneaux de la classe.
        404 — Aucun créneau trouvé pour cette classe.
        500 — Erreur serveur.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = """
                SELECT edt_id, topic_name, room_name, teacher_l_name, teacher_f_name,
                       class_name, start_time, end_time
                FROM EDT
                WHERE class_name = %s
                ORDER BY start_time ASC
            """
            cursor.execute(sql, (class_name,))
            edt_list = cursor.fetchall()

        if edt_list:
            # Conversion des datetime en chaînes pour la sérialisation JSON
            for entry in edt_list:
                if entry.get("start_time"):
                    entry["start_time"] = entry["start_time"].strftime("%Y-%m-%d %H:%M:%S")
                if entry.get("end_time"):
                    entry["end_time"] = entry["end_time"].strftime("%Y-%m-%d %H:%M:%S")

            return jsonify({"class_name": class_name, "edt": edt_list}), 200
        else:
            return jsonify({"error": f"Aucun emploi du temps trouvé pour la classe '{class_name}'."}), 404

    except Exception as e:
        return jsonify({"error": f"Erreur serveur : {str(e)}"}), 500
    finally:
        if conn:
            conn.close()


# ──────────────────────────────────────────────
# GET /api/edt/teacher/<teacher_l_name>
# ──────────────────────────────────────────────
@edt_bp.route("/edt/teacher/<string:teacher_l_name>", methods=["GET"])
def get_edt_by_teacher(teacher_l_name):
    """
    Récupère l'emploi du temps d'un professeur (par son nom de famille).

    Retourne :
        200 — Liste des créneaux du professeur.
        404 — Aucun créneau trouvé pour ce professeur.
        500 — Erreur serveur.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = """
                SELECT edt_id, topic_name, room_name, teacher_l_name, teacher_f_name,
                       class_name, start_time, end_time
                FROM EDT
                WHERE teacher_l_name = %s
                ORDER BY start_time ASC
            """
            cursor.execute(sql, (teacher_l_name,))
            edt_list = cursor.fetchall()

        if edt_list:
            for entry in edt_list:
                if entry.get("start_time"):
                    entry["start_time"] = entry["start_time"].strftime("%Y-%m-%d %H:%M:%S")
                if entry.get("end_time"):
                    entry["end_time"] = entry["end_time"].strftime("%Y-%m-%d %H:%M:%S")

            return jsonify({"teacher_l_name": teacher_l_name, "edt": edt_list}), 200
        else:
            return jsonify({"error": f"Aucun emploi du temps trouvé pour le professeur '{teacher_l_name}'."}), 404

    except Exception as e:
        return jsonify({"error": f"Erreur serveur : {str(e)}"}), 500
    finally:
        if conn:
            conn.close()


# ──────────────────────────────────────────────
# POST /api/edt
# ──────────────────────────────────────────────
@edt_bp.route("/edt", methods=["POST"])
def create_edt_entry():
    """
    Ajoute une nouvelle entrée dans l'emploi du temps.

    Body JSON attendu :
        {
            "topic_name": "...",
            "room_name": "...",
            "teacher_l_name": "...",
            "teacher_f_name": "...",
            "class_name": "...",
            "start_time": "YYYY-MM-DD HH:MM:SS",
            "end_time": "YYYY-MM-DD HH:MM:SS"
        }

    Retourne :
        201 — Entrée créée avec succès.
        400 — Champs manquants.
        500 — Erreur serveur.
    """
    data = request.get_json()

    # --- Validation des champs requis ---
    required_fields = ["topic_name", "room_name", "teacher_l_name",
                       "teacher_f_name", "class_name", "start_time", "end_time"]
    missing = [f for f in required_fields if not data or not data.get(f)]
    if missing:
        return jsonify({"error": f"Champs manquants : {', '.join(missing)}"}), 400

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO EDT (topic_name, room_name, teacher_l_name, teacher_f_name,
                                 class_name, start_time, end_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                data["topic_name"],
                data["room_name"],
                data["teacher_l_name"],
                data["teacher_f_name"],
                data["class_name"],
                data["start_time"],
                data["end_time"]
            ))
        conn.commit()

        return jsonify({"message": "Entrée EDT ajoutée avec succès."}), 201

    except Exception as e:
        return jsonify({"error": f"Erreur serveur : {str(e)}"}), 500
    finally:
        if conn:
            conn.close()
