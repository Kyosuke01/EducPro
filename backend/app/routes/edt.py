"""
routes/edt.py — Routes pour la gestion des emplois du temps (EDT).

Endpoints :
    GET  /api/edt                           — Tous les créneaux EDT
    GET  /api/edt/class/<class_name>        — EDT d'une classe
    GET  /api/edt/teacher/<teacher_l_name>  — EDT d'un professeur
    POST /api/edt                           — Ajouter une entrée EDT
"""

from flask import Blueprint, request, jsonify
from app.db import get_db_connection
from app.rbac import require_role

edt_bp = Blueprint("edt", __name__)


def _serialize_edt(edt_list):
    """Convertit les datetime en chaînes pour tous les créneaux."""
    for entry in edt_list:
        if entry.get("start_time"):
            entry["start_time"] = entry["start_time"].strftime("%Y-%m-%d %H:%M:%S")
        if entry.get("end_time"):
            entry["end_time"] = entry["end_time"].strftime("%Y-%m-%d %H:%M:%S")
    return edt_list

# GET /api/edt


@edt_bp.route("/edt", methods=["GET"])
def get_all_edt():
    """Récupère tous les créneaux EDT."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = """
                SELECT edt_id, topic_name, room_name, teacher_l_name, teacher_f_name,
                       class_name, start_time, end_time
                FROM EDT
                ORDER BY start_time ASC
            """
            cursor.execute(sql)
            edt_list = cursor.fetchall()

        return jsonify({"edt": _serialize_edt(edt_list)}), 200

    except Exception as e:
        return jsonify({"error": f"Erreur serveur : {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

# GET /api/edt/class/<class_name>


@edt_bp.route("/edt/class/<string:class_name>", methods=["GET"])
def get_edt_by_class(class_name):
    """Récupère l'emploi du temps complet d'une classe donnée."""
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

        return jsonify({"class_name": class_name, "edt": _serialize_edt(edt_list)}), 200

    except Exception as e:
        return jsonify({"error": f"Erreur serveur : {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

# GET /api/edt/teacher/<teacher_l_name>


@edt_bp.route("/edt/teacher/<string:teacher_l_name>", methods=["GET"])
def get_edt_by_teacher(teacher_l_name):
    """Récupère l'emploi du temps d'un professeur (par son nom de famille)."""
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

        return jsonify({"teacher_l_name": teacher_l_name, "edt": _serialize_edt(edt_list)}), 200

    except Exception as e:
        return jsonify({"error": f"Erreur serveur : {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

# POST /api/edt


@edt_bp.route("/edt", methods=["POST"])
@require_role('admin')
def create_edt_entry():
    """Ajoute une nouvelle entrée dans l'emploi du temps."""
    data = request.get_json()

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
