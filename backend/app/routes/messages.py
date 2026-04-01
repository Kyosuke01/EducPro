"""routes/messages.py — Messagerie & tickets multi-étapes."""

from flask import Blueprint, request, jsonify
from app.db import get_db_connection

messages_bp = Blueprint("messages", __name__)


def _serialize_dt(value):
    if value is None:
        return None
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def _valid_role(role):
    return role in {"student", "teacher", "admin"}


# ──────────────────────────────────────────────
# GET /api/notifications
# ──────────────────────────────────────────────
@messages_bp.route("/notifications", methods=["GET"])
def get_notifications():
    """Renvoie une petite liste de notifications mockées pour l'UI."""
    limit = request.args.get("limit", 5, type=int)
    sample = [
        {"title": "Bienvenue", "body": "Votre compte est prêt.", "type": "system"},
        {"title": "Profil", "body": "Pensez à compléter vos informations.", "type": "message"},
        {"title": "Sécurité", "body": "Activez l'A2F pour protéger votre compte.", "type": "alert"},
        {"title": "Rappel", "body": "Consultez les dernières mises à jour.", "type": "info"},
    ]
    return jsonify({"notifications": sample[:limit]}), 200


# ──────────────────────────────────────────────
# GET /api/messages/recipients
# ──────────────────────────────────────────────
@messages_bp.route("/messages/recipients", methods=["GET"])
def search_recipients():
    target = request.args.get("type", "all")
    query = (request.args.get("q", "") or "").strip()
    like_query = f"%{query}%"
    limit = min(request.args.get("limit", 15, type=int), 50)

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            if target == "all":
                cursor.execute(
                    """
                    SELECT teacher_id AS id, first_name, last_name, mail_teacher AS email, topic_name AS meta, 'teacher' AS role FROM Teacher
                    WHERE %s = '' OR first_name LIKE %s OR last_name LIKE %s OR mail_teacher LIKE %s
                    UNION ALL
                    SELECT student_id AS id, first_name, last_name, mail_student AS email, class_name AS meta, 'student' AS role FROM Student
                    WHERE %s = '' OR first_name LIKE %s OR last_name LIKE %s OR mail_student LIKE %s
                    ORDER BY last_name ASC, first_name ASC
                    LIMIT %s
                    """,
                    (query, like_query, like_query, like_query, query, like_query, like_query, like_query, limit)
                )
            else:
                table_conf = {
                    "teacher": {
                        "table": "Teacher",
                        "fields": "teacher_id AS id, first_name, last_name, mail_teacher AS email, topic_name AS meta, 'teacher' AS role",
                        "email_column": "mail_teacher"
                    },
                    "student": {
                        "table": "Student",
                        "fields": "student_id AS id, first_name, last_name, mail_student AS email, class_name AS meta, 'student' AS role",
                        "email_column": "mail_student"
                    }
                }
                if target not in table_conf:
                    return jsonify({"error": "Type de recherche invalide."}), 400

                cfg = table_conf[target]
                cursor.execute(
                    f"""
                    SELECT {cfg['fields']}
                    FROM {cfg['table']}
                    WHERE %s = '' OR first_name LIKE %s OR last_name LIKE %s OR {cfg['email_column']} LIKE %s
                    ORDER BY last_name ASC, first_name ASC
                    LIMIT %s
                    """,
                    (query, like_query, like_query, like_query, limit)
                )
            results = cursor.fetchall()

        return jsonify({"results": results}), 200
    except Exception as e:
        return jsonify({"error": f"Erreur serveur : {str(e)}"}), 500
    finally:
        if conn:
            conn.close()


# ──────────────────────────────────────────────
# GET /api/messages/conversations
# ──────────────────────────────────────────────
@messages_bp.route("/messages/conversations", methods=["GET"])
def list_conversations():
    role = request.args.get("role")
    user_id = request.args.get("user_id", type=int)

    if not _valid_role(role) or not user_id:
        return jsonify({"error": "Paramètres role et user_id requis."}), 400

    filters = []
    params = []
    if role == "student":
        filters.append("(st.student_id = %s OR (st.created_by_role = 'student' AND st.created_by_id = %s))")
        params.extend([user_id, user_id])
    elif role == "teacher":
        filters.append("(st.teacher_id = %s OR (st.created_by_role = 'teacher' AND st.created_by_id = %s))")
        params.extend([user_id, user_id])
    elif role == "admin":
        filters.append("((st.student_id IS NULL AND st.teacher_id IS NULL) OR st.created_by_role = 'admin')")

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT st.ticket_id, st.subject, st.status, st.priority, st.created_at, st.updated_at,
                         st.student_id, st.teacher_id, st.created_by_role, st.created_by_id,
                       s.first_name AS student_first_name, s.last_name AS student_last_name,
                       t.first_name AS teacher_first_name, t.last_name AS teacher_last_name,
                       lm.last_body AS last_message,
                       lm.last_created_at AS last_message_at
                FROM SupportTicket st
                LEFT JOIN Student s ON st.student_id = s.student_id
                LEFT JOIN Teacher t ON st.teacher_id = t.teacher_id
                LEFT JOIN (
                    SELECT ticket_id,
                           MAX(created_at) AS last_created_at,
                           SUBSTRING_INDEX(GROUP_CONCAT(body ORDER BY created_at DESC SEPARATOR '§§'), '§§', 1) AS last_body
                    FROM SupportMessage
                    GROUP BY ticket_id
                ) lm ON lm.ticket_id = st.ticket_id
                {where_clause}
                ORDER BY st.updated_at DESC
                """,
                params
            )
            tickets = cursor.fetchall()

        for ticket in tickets:
            ticket["last_message_at"] = _serialize_dt(ticket.get("last_message_at"))
            ticket["created_at"] = _serialize_dt(ticket.get("created_at"))
            ticket["updated_at"] = _serialize_dt(ticket.get("updated_at"))

        return jsonify({"tickets": tickets}), 200
    except Exception as e:
        return jsonify({"error": f"Erreur serveur : {str(e)}"}), 500
    finally:
        if conn:
            conn.close()


# ──────────────────────────────────────────────
# GET /api/messages/conversations/<id>
# ──────────────────────────────────────────────
@messages_bp.route("/messages/conversations/<int:ticket_id>", methods=["GET"])
def get_conversation(ticket_id):
    role = request.args.get("role")
    user_id = request.args.get("user_id", type=int)

    if not _valid_role(role) or not user_id:
        return jsonify({"error": "Paramètres role et user_id requis."}), 400

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT st.ticket_id, st.subject, st.status, st.priority, st.created_at, st.updated_at,
                       st.student_id, st.teacher_id,
                       s.first_name AS student_first_name, s.last_name AS student_last_name,
                       t.first_name AS teacher_first_name, t.last_name AS teacher_last_name
                FROM SupportTicket st
                LEFT JOIN Student s ON st.student_id = s.student_id
                LEFT JOIN Teacher t ON st.teacher_id = t.teacher_id
                WHERE st.ticket_id = %s
                """,
                (ticket_id,)
            )
            ticket = cursor.fetchone()

            if not ticket:
                return jsonify({"error": "Ticket introuvable."}), 404

            # Contrôle d'accès minimal
            if role == "student" and ticket.get("student_id") != user_id and not (ticket.get("created_by_role") == "student" and ticket.get("created_by_id") == user_id):
                return jsonify({"error": "Accès refusé."}), 403
            if role == "teacher" and ticket.get("teacher_id") != user_id and not (ticket.get("created_by_role") == "teacher" and ticket.get("created_by_id") == user_id):
                return jsonify({"error": "Accès refusé."}), 403

            cursor.execute(
                """
                SELECT message_id, sender_role, sender_id, body, created_at
                FROM SupportMessage
                WHERE ticket_id = %s
                ORDER BY created_at ASC
                """,
                (ticket_id,)
            )
            messages = cursor.fetchall()

        ticket["created_at"] = _serialize_dt(ticket.get("created_at"))
        ticket["updated_at"] = _serialize_dt(ticket.get("updated_at"))
        for msg in messages:
            msg["created_at"] = _serialize_dt(msg.get("created_at"))

        return jsonify({"ticket": ticket, "messages": messages}), 200
    except Exception as e:
        return jsonify({"error": f"Erreur serveur : {str(e)}"}), 500
    finally:
        if conn:
            conn.close()


# ──────────────────────────────────────────────
# POST /api/messages/conversations
# ──────────────────────────────────────────────
@messages_bp.route("/messages/conversations", methods=["POST"])
def create_conversation():
    data = request.get_json() or {}
    subject = (data.get("subject") or "Demande d'assistance").strip()
    message = (data.get("message") or "").strip()
    starter_role = data.get("starter_role")
    starter_id = data.get("starter_id")
    recipient_role = data.get("recipient_role")
    recipient_id = data.get("recipient_id")

    if not subject or not message or not _valid_role(starter_role) or not starter_id:
        return jsonify({"error": "Champs invalides."}), 400

    # Convert generic sender/recipient to student/teacher if applicable
    student_id = None
    teacher_id = None

    if starter_role == "student":
        student_id = starter_id
    elif starter_role == "teacher":
        teacher_id = starter_id
    elif starter_role == "admin":
        pass  # Pas de colonne dédiée

    if recipient_role == "student":
        student_id = recipient_id
    elif recipient_role == "teacher":
        teacher_id = recipient_id
    elif recipient_role == "admin":
        pass

    # Remove strict student/teacher constraint to allow all role combinations
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO SupportTicket (subject, student_id, teacher_id, created_by_role, created_by_id)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (subject, student_id, teacher_id, starter_role, starter_id)
            )
            ticket_id = cursor.lastrowid

            cursor.execute(
                "INSERT INTO SupportMessage (ticket_id, sender_role, sender_id, body) VALUES (%s, %s, %s, %s)",
                (ticket_id, starter_role, starter_id, message)
            )

            conn.commit()

        return jsonify({"ticket_id": ticket_id, "message": "Ticket créé."}), 201
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"error": f"Erreur serveur : {str(e)}"}), 500
    finally:
        if conn:
            conn.close()


# ──────────────────────────────────────────────
# POST /api/messages/conversations/<id>/messages
# ──────────────────────────────────────────────
@messages_bp.route("/messages/conversations/<int:ticket_id>/messages", methods=["POST"])
def append_message(ticket_id):
    data = request.get_json() or {}
    body = (data.get("body") or "").strip()
    sender_role = data.get("sender_role")
    sender_id = data.get("sender_id")

    if not body or not _valid_role(sender_role) or not sender_id:
        return jsonify({"error": "Champs body, sender_role et sender_id requis."}), 400

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT student_id, teacher_id, created_by_role, created_by_id FROM SupportTicket WHERE ticket_id = %s",
                (ticket_id,)
            )
            ticket = cursor.fetchone()
            if not ticket:
                return jsonify({"error": "Ticket introuvable."}), 404

            if sender_role == "student" and ticket.get("student_id") != sender_id and not (ticket.get("created_by_role") == "student" and ticket.get("created_by_id") == sender_id):
                return jsonify({"error": "Accès refusé."}), 403
            if sender_role == "teacher" and ticket.get("teacher_id") != sender_id and not (ticket.get("created_by_role") == "teacher" and ticket.get("created_by_id") == sender_id):
                return jsonify({"error": "Accès refusé."}), 403

            cursor.execute(
                "INSERT INTO SupportMessage (ticket_id, sender_role, sender_id, body) VALUES (%s, %s, %s, %s)",
                (ticket_id, sender_role, sender_id, body)
            )
            cursor.execute(
                "UPDATE SupportTicket SET updated_at = CURRENT_TIMESTAMP WHERE ticket_id = %s",
                (ticket_id,)
            )
            conn.commit()

        return jsonify({"message": "Réponse ajoutée."}), 201
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"error": f"Erreur serveur : {str(e)}"}), 500
    finally:
        if conn:
            conn.close()
