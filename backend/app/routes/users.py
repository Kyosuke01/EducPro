from flask import Blueprint, jsonify, request
from app.db import get_db_connection
from app.rbac import require_role
import bcrypt

users_bp = Blueprint("users", __name__)

def _class_has_capacity(conn, class_name, exclude_student_id=None):
    if not class_name:
        return False

    with conn.cursor() as cursor:
        cursor.execute("SELECT max_capacity FROM Class WHERE name = %s", (class_name,))
        class_row = cursor.fetchone()
        if not class_row:
            raise ValueError("Classe introuvable")

        query = "SELECT COUNT(*) AS total FROM Student WHERE class_name = %s"
        params = [class_name]
        if exclude_student_id:
            query += " AND student_id <> %s"
            params.append(exclude_student_id)

        cursor.execute(query, params)
        total = cursor.fetchone()["total"] or 0

        return total < class_row["max_capacity"]

# GET tous les utilisateurs (Étudiants + Professeurs)

@users_bp.route("/", methods=["GET"])
def get_users():
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Récupérer les étudiants
            cursor.execute("SELECT first_name, last_name, mail_student as email, 'student' as role FROM Student")
            students = cursor.fetchall()

            # Récupérer les professeurs
            cursor.execute("SELECT first_name, last_name, mail_teacher as email, 'teacher' as role FROM Teacher")
            teachers = cursor.fetchall()

            # Fusionner
            users = []
            for s in students:
                users.append({"username": f"{s['first_name']} {s['last_name']}",
                             "email": s['email'], "role": s['role']})
            for t in teachers:
                users.append({"username": f"{t['first_name']} {t['last_name']}",
                             "email": t['email'], "role": t['role']})

        return jsonify(users), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

# POST créer un utilisateur (Sécurisé par accès Admin)

def _validate_user_data(data):
    """Validate required fields and return parsed data."""
    user_type = data.get("user_type")
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    email = data.get("email")
    password = data.get("password")

    if not all([user_type, first_name, last_name, email, password]):
        return None, jsonify({"error": "Tous les champs (nom, prénom, email, mot de passe) sont requis."}), 400

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(14)).decode('utf-8')
    return {
        "user_type": user_type,
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "hashed_password": hashed_password
    }, None, None

def _create_student(cursor, conn, user_data, data):
    """Create a student user."""
    class_name = data.get("class_name")
    if not class_name:
        return False, jsonify({"error": "La classe est requise pour un étudiant."}), 400

    try:
        if not _class_has_capacity(conn, class_name):
            return False, jsonify({"error": "Cette classe a atteint sa capacité maximale (35 élèves)."}), 400
    except ValueError as err:
        return False, jsonify({"error": str(err)}), 400

    sql_insert = (
        "INSERT INTO Student "
        "(first_name, last_name, mail_student, password, class_name) "
        "VALUES (%s, %s, %s, %s, %s)"
    )
    cursor.execute(sql_insert, (
        user_data["first_name"],
        user_data["last_name"],
        user_data["email"],
        user_data["hashed_password"],
        class_name
    ))
    return True, None, None

def _create_teacher(cursor, user_data, data):
    """Create a teacher user."""
    topic_name = data.get("topic_name")
    if not topic_name:
        return False, jsonify({"error": "La matière est requise pour un professeur."}), 400

    sql_insert = (
        "INSERT INTO Teacher "
        "(first_name, last_name, mail_teacher, password, topic_name, is_admin) "
        "VALUES (%s, %s, %s, %s, %s, 0)"
    )
    cursor.execute(sql_insert, (
        user_data["first_name"],
        user_data["last_name"],
        user_data["email"],
        user_data["hashed_password"],
        topic_name
    ))
    return True, None, None

@users_bp.route("/", methods=["POST"])
@require_role('admin')
def create_user():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Données invalides."}), 400

    user_data, error_resp, error_code = _validate_user_data(data)
    if error_resp is not None:
        return error_resp, error_code

    user_type = user_data["user_type"]
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            if user_type == "student":
                is_ok, err_resp, err_code = _create_student(cursor, conn, user_data, data)
                if not is_ok:
                    return err_resp, err_code
            elif user_type == "teacher":
                is_ok, err_resp, err_code = _create_teacher(cursor, user_data, data)
                if not is_ok:
                    return err_resp, err_code
            else:
                return jsonify({"error": "Type d'utilisateur invalide."}), 400

            conn.commit()
            return jsonify({"message": f"Utilisateur ({user_type}) créé avec succès."}), 201

    except Exception as e:
        if "Duplicate entry" in str(e):
            return jsonify({"error": "Cet email est déjà utilisé."}), 409
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

# PUT modifier un utilisateur

@users_bp.route("/<user_type>/<int:user_id>", methods=["PUT"])
@require_role('admin')
def update_user(user_type, user_id):
    data = request.get_json()
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    email = data.get("email")

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            if user_type == "student":
                class_name = data.get("class_name")
                if class_name:
                    try:
                        if not _class_has_capacity(conn, class_name, exclude_student_id=user_id):
                            msg = "Impossible de déplacer l'étudiant : classe complète."
                            return jsonify({"error": msg}), 400
                    except ValueError as err:
                        return jsonify({"error": str(err)}), 400
                sql_update = (
                    "UPDATE Student SET first_name=%s, last_name=%s, "
                    "mail_student=%s, class_name=%s WHERE student_id=%s"
                )
                cursor.execute(
                    sql_update,
                    (first_name, last_name, email, class_name, user_id)
                )
            elif user_type == "teacher":
                topic_name = data.get("topic_name")
                sql_update = (
                    "UPDATE Teacher SET first_name=%s, last_name=%s, "
                    "mail_teacher=%s, topic_name=%s WHERE teacher_id=%s"
                )
                cursor.execute(
                    sql_update,
                    (first_name, last_name, email, topic_name, user_id)
                )
            else:
                return jsonify({"error": "Type utilisateur invalide."}), 400
            conn.commit()
            return jsonify({"message": "Utilisateur mis à jour avec succès."}), 200
    except Exception as e:
        if "Duplicate entry" in str(e):
            return jsonify({"error": "Cet email est déjà pris."}), 409
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

# DELETE supprimer un utilisateur

@users_bp.route("/<user_type>/<int:user_id>", methods=["DELETE"])
@require_role('admin')
def delete_user(user_type, user_id):
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            if user_type == "student":
                cursor.execute("DELETE FROM Grade WHERE student_id=%s", (user_id,))
                cursor.execute("DELETE FROM Attendance WHERE student_id=%s", (user_id,))
                cursor.execute("DELETE FROM Student WHERE student_id=%s", (user_id,))
            elif user_type == "teacher":
                cursor.execute("DELETE FROM Topic WHERE teacher_id=%s", (user_id,))
                cursor.execute("DELETE FROM Teacher WHERE teacher_id=%s", (user_id,))
            else:
                return jsonify({"error": "Type utilisateur invalide."}), 400
            conn.commit()
            return jsonify({"message": "Utilisateur supprimé avec succès."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()
