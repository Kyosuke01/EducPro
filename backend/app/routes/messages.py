"""
routes/messages.py — Routes pour la gestion de la messagerie (Table TICKET).
"""

from flask import Blueprint, request, jsonify
from app.db import get_db_connection

messages_bp = Blueprint("messages", __name__)

# ──────────────────────────────────────────────
# GET /api/notifications
# ──────────────────────────────────────────────
@messages_bp.route("/notifications", methods=["GET"])
def get_notifications():
    """Renvoie une petite liste de notifications mockées pour l'UI."""
    # On autorise un filtre limit tout en restant tolérant
    limit = request.args.get("limit", 5, type=int)
    sample = [
        {"title": "Bienvenue", "body": "Votre compte est prêt.", "type": "system"},
        {"title": "Profil", "body": "Pensez à compléter vos informations.", "type": "message"},
        {"title": "Sécurité", "body": "Activez l'A2F pour protéger votre compte.", "type": "alert"},
        {"title": "Rappel", "body": "Consultez les dernières mises à jour.", "type": "info"},
    ]
    return jsonify({"notifications": sample[:limit]}), 200

# ──────────────────────────────────────────────
# GET /api/messages/student/<int:student_id>
# ──────────────────────────────────────────────
@messages_bp.route("/messages/student/<int:student_id>", methods=["GET"])
def get_messages_by_student(student_id):
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = """
                SELECT t.ticket_id, t.msg_content, t.teacher_id, t.student_id, 
                       tr.first_name as teacher_first_name, tr.last_name as teacher_last_name
                FROM TICKET t
                JOIN Teacher tr ON t.teacher_id = tr.teacher_id
                WHERE t.student_id = %s
                ORDER BY t.ticket_id ASC
            """
            cursor.execute(sql, (student_id,))
            messages = cursor.fetchall()
        return jsonify({"student_id": student_id, "messages": messages}), 200
    except Exception as e:
        return jsonify({"error": f"Erreur serveur : {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

# ──────────────────────────────────────────────
# GET /api/messages/teacher/<int:teacher_id>
# ──────────────────────────────────────────────
@messages_bp.route("/messages/teacher/<int:teacher_id>", methods=["GET"])
def get_messages_by_teacher(teacher_id):
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = """
                SELECT t.ticket_id, t.msg_content, t.teacher_id, t.student_id, 
                       s.first_name as student_first_name, s.last_name as student_last_name, s.class_name
                FROM TICKET t
                JOIN Student s ON t.student_id = s.student_id
                WHERE t.teacher_id = %s
                ORDER BY t.ticket_id ASC
            """
            cursor.execute(sql, (teacher_id,))
            messages = cursor.fetchall()
        return jsonify({"teacher_id": teacher_id, "messages": messages}), 200
    except Exception as e:
        return jsonify({"error": f"Erreur serveur : {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

# ──────────────────────────────────────────────
# POST /api/messages
# ──────────────────────────────────────────────
@messages_bp.route("/messages", methods=["POST"])
def send_message():
    data = request.get_json()
    msg_content = data.get("msg_content")
    teacher_id = data.get("teacher_id")
    student_id = data.get("student_id")

    if not msg_content or not teacher_id or not student_id:
        return jsonify({"error": "Champs manquants"}), 400

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = "INSERT INTO TICKET (msg_content, teacher_id, student_id) VALUES (%s, %s, %s)"
            cursor.execute(sql, (msg_content, teacher_id, student_id))
            conn.commit()
            new_id = cursor.lastrowid
        return jsonify({"success": True, "ticket_id": new_id, "message": "Message envoyé"}), 201
    except Exception as e:
        return jsonify({"error": f"Erreur serveur : {str(e)}"}), 500
    finally:
        if conn:
            conn.close()
