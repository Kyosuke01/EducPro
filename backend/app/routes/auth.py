"""
routes/auth.py — Routes d'authentification et de profils (étudiants/professeurs).

Endpoints :
    POST /api/auth/login              — Connexion unifiée (étudiant ou professeur/admin)
    GET  /api/students                — Liste de tous les étudiants
    GET  /api/students/<int:id>       — Infos d'un étudiant
    GET  /api/teachers                — Liste de tous les professeurs
    GET  /api/teachers/<int:id>       — Infos d'un professeur
"""

from flask import Blueprint, request, jsonify
from app.db import get_db_connection
import bcrypt
import pyotp

auth_bp = Blueprint("auth", __name__)


# ──────────────────────────────────────────────
# POST /api/auth/login
# ──────────────────────────────────────────────
@auth_bp.route("/auth/login", methods=["POST"])
def login():
    """
    Authentification unifiée : cherche d'abord dans Student, puis Teacher.

    Body JSON attendu :
        { "email": "...", "password": "..." }

    Retourne :
        200 — Succès avec les infos utilisateur et le rôle.
        401 — Identifiants invalides.
        400 — Champs manquants.
        500 — Erreur serveur.
    """
    data = request.get_json()

    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"error": "Les champs 'email' et 'password' sont requis."}), 400

    email = data["email"]
    password = data["password"]

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 1) Chercher dans Student
            cursor.execute(
                "SELECT student_id, first_name, last_name, mail_student, class_name, password, totp_secret "
                "FROM Student WHERE mail_student = %s",
                (email,)
            )
            student = cursor.fetchone()

            if student and bcrypt.checkpw(password.encode('utf-8'), student["password"].encode('utf-8')):
                return jsonify({
                    "message": "Connexion réussie.",
                    "user": {
                        "id": student["student_id"],
                        "first_name": student["first_name"],
                        "last_name": student["last_name"],
                        "email": student["mail_student"],
                        "class_name": student.get("class_name"),
                        "role": "student",
                        "has_2fa": bool(student.get("totp_secret"))
                    }
                }), 200

            # 2) Chercher dans Teacher
            cursor.execute(
                "SELECT teacher_id, first_name, last_name, mail_teacher, is_admin, topic_name, password, totp_secret "
                "FROM Teacher WHERE mail_teacher = %s",
                (email,)
            )
            teacher = cursor.fetchone()

            if teacher and bcrypt.checkpw(password.encode('utf-8'), teacher["password"].encode('utf-8')):
                role = "admin" if teacher.get("is_admin") else "teacher"

                return jsonify({
                    "message": "Connexion réussie.",
                    "user": {
                        "id": teacher["teacher_id"],
                        "first_name": teacher["first_name"],
                        "last_name": teacher["last_name"],
                        "email": teacher["mail_teacher"],
                        "topic_name": teacher.get("topic_name"),
                        "role": role,
                        "has_2fa": bool(teacher.get("totp_secret"))
                    }
                }), 200

            # Aucun match ou mauvais mot de passe
            return jsonify({"error": "Email ou mot de passe incorrect."}), 401

    except Exception as e:
        return jsonify({"error": f"Erreur serveur : {str(e)}"}), 500
    finally:
        if conn:
            conn.close()


# ──────────────────────────────────────────────
# GET /api/students
# ──────────────────────────────────────────────
@auth_bp.route("/students", methods=["GET"])
def get_all_students():
    """Liste de tous les étudiants."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT student_id, first_name, last_name, mail_student, class_name, dob "
                "FROM Student ORDER BY last_name, first_name"
            )
            students = cursor.fetchall()

        # Convertir les dates
        for s in students:
            if s.get("dob"):
                s["dob"] = s["dob"].strftime("%Y-%m-%d")

        return jsonify({"students": students}), 200

    except Exception as e:
        return jsonify({"error": f"Erreur serveur : {str(e)}"}), 500
    finally:
        if conn:
            conn.close()


# ──────────────────────────────────────────────
# GET /api/students/<int:id>
# ──────────────────────────────────────────────
@auth_bp.route("/students/<int:id>", methods=["GET"])
def get_student(id):
    """Récupère les informations d'un étudiant par son identifiant."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT student_id, first_name, last_name, mail_student, class_name "
                "FROM Student WHERE student_id = %s",
                (id,)
            )
            student = cursor.fetchone()

        if student:
            return jsonify(student), 200
        else:
            return jsonify({"error": "Étudiant non trouvé."}), 404

    except Exception as e:
        return jsonify({"error": f"Erreur serveur : {str(e)}"}), 500
    finally:
        if conn:
            conn.close()


# ──────────────────────────────────────────────
# GET /api/teachers
# ──────────────────────────────────────────────
@auth_bp.route("/teachers", methods=["GET"])
def get_all_teachers():
    """Liste de tous les professeurs."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT teacher_id, first_name, last_name, mail_teacher, topic_name, is_admin "
                "FROM Teacher ORDER BY last_name, first_name"
            )
            teachers = cursor.fetchall()

        return jsonify({"teachers": teachers}), 200

    except Exception as e:
        return jsonify({"error": f"Erreur serveur : {str(e)}"}), 500
    finally:
        if conn:
            conn.close()


# ──────────────────────────────────────────────
# GET /api/teachers/<int:id>
# ──────────────────────────────────────────────
@auth_bp.route("/teachers/<int:id>", methods=["GET"])
def get_teacher(id):
    """Récupère les informations d'un professeur par son identifiant."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT teacher_id, first_name, last_name, mail_teacher, topic_name, is_admin "
                "FROM Teacher WHERE teacher_id = %s",
                (id,)
            )
            teacher = cursor.fetchone()

        if teacher:
            return jsonify(teacher), 200
        else:
            return jsonify({"error": "Professeur non trouvé."}), 404

    except Exception as e:
        return jsonify({"error": f"Erreur serveur : {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

# ──────────────────────────────────────────────
# 2FA & PASSWORD ENDPOINTS
# ──────────────────────────────────────────────

@auth_bp.route("/auth/2fa/generate", methods=["GET"])
def generate_2fa():
    """
    Génère un nouveau secret pyotp et l'URI pour le QR code.
    Paramètres GET : app_name, email (optionnels pour formatage de l'URI).
    """
    secret = pyotp.random_base32()
    # On pourrait aussi extraire l'email en query string pour formater un beau QR code
    email = request.args.get("email", "User")
    uri = pyotp.totp.TOTP(secret).provisioning_uri(name=email, issuer_name="EducPro")
    return jsonify({"secret": secret, "uri": uri}), 200

@auth_bp.route("/auth/2fa/verify", methods=["POST"])
def verify_2fa():
    """
    Prend le secret généré et le code tapé par l'utilisateur.
    Body JSON attendu : { "user_id": 1, "role": "admin/teacher/student", "secret": "...", "code": "..." }
    """
    data = request.get_json()
    if not data or not all(k in data for k in ("user_id", "role", "secret", "code")):
        return jsonify({"error": "Champs user_id, role, secret, code requis"}), 400

    totp = pyotp.TOTP(data["secret"])
    if not totp.verify(data["code"]):
        return jsonify({"error": "Code TOTP invalide"}), 400

    table = "Teacher" if data["role"] in ["teacher", "admin"] else "Student"
    id_field = "teacher_id" if table == "Teacher" else "student_id"

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            query = f"UPDATE {table} SET totp_secret = %s WHERE {id_field} = %s"
            cursor.execute(query, (data["secret"], data["user_id"]))
            conn.commit()
        return jsonify({"message": "2FA activé avec succès"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

@auth_bp.route("/auth/forgot-password", methods=["POST"])
def forgot_password():
    """
    Recherche l'email dans Student ou Teacher.
    Vérifie si totp_secret existe.
    Body JSON : { "email": "..." }
    """
    data = request.get_json()
    email = data.get("email")
    if not email: return jsonify({"error": "Email requis"}), 400

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Chercher dans Student
            cursor.execute("SELECT student_id as id, 'student' as role, totp_secret FROM Student WHERE mail_student = %s", (email,))
            user = cursor.fetchone()
            if not user:
                cursor.execute("SELECT teacher_id as id, 'teacher' as role, totp_secret FROM Teacher WHERE mail_teacher = %s", (email,))
                user = cursor.fetchone()

        if not user:
            # On renvoie 200 par sécurité anti-scan email (ou 200 avec message)
            return jsonify({"message": "Si le compte existe, l'étape suivante est requise."}), 200

        if not user.get("totp_secret"):
            return jsonify({"error": "Ce compte n'a pas configuré l'A2F. Contactez un administrateur."}), 403

        return jsonify({"message": "Veuillez fournir le code 2FA pour réinitialiser le mot de passe."}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

@auth_bp.route("/auth/reset-password", methods=["POST"])
def reset_password():
    """
    Reçoit (email, code_a2f, new_password).
    """
    data = request.get_json()
    email = data.get("email")
    code_a2f = data.get("code_a2f")
    new_pwd = data.get("new_password")

    if not all([email, code_a2f, new_pwd]):
        return jsonify({"error": "email, code_a2f et new_password requis"}), 400

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Identifier la table
            cursor.execute("SELECT student_id as id, 'Student' as tbl, totp_secret FROM Student WHERE mail_student = %s", (email,))
            user = cursor.fetchone()
            id_field = "student_id"
            if not user:
                cursor.execute("SELECT teacher_id as id, 'Teacher' as tbl, totp_secret FROM Teacher WHERE mail_teacher = %s", (email,))
                user = cursor.fetchone()
                id_field = "teacher_id"

        if not user or not user.get("totp_secret"):
            return jsonify({"error": "Compte introuvable ou A2F non configuré."}), 400

        # Verif TOTP
        totp = pyotp.TOTP(user["totp_secret"])
        if not totp.verify(code_a2f):
            return jsonify({"error": "Code TOTP invalide"}), 400

        # Update mot de passe
        hashed = bcrypt.hashpw(new_pwd.encode('utf-8'), bcrypt.gensalt(14)).decode('utf-8')
        with conn.cursor() as cursor:
            query = f"UPDATE {user['tbl']} SET password = %s WHERE {id_field} = %s"
            cursor.execute(query, (hashed, user['id']))
            conn.commit()

        return jsonify({"message": "Mot de passe réinitialisé avec succès."}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

@auth_bp.route("/users/change-password", methods=["POST"])
def change_password():
    """
    Changement classique du MDP via paramètres.
    Body JSON : { "user_id": 1, "role": "student/teacher/admin", "old_password": "...", "new_password": "..." }
    """
    data = request.get_json()
    if not all(k in data for k in ("user_id", "role", "old_password", "new_password")):
        return jsonify({"error": "user_id, role, old_password, new_password requis"}), 400

    table = "Teacher" if data["role"] in ["teacher", "admin"] else "Student"
    id_field = "teacher_id" if table == "Teacher" else "student_id"

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT password FROM {table} WHERE {id_field} = %s", (data["user_id"],))
            user = cursor.fetchone()

            if not user or not bcrypt.checkpw(data["old_password"].encode('utf-8'), user["password"].encode('utf-8')):
                return jsonify({"error": "Ancien mot de passe incorrect"}), 400

            hashed = bcrypt.hashpw(data["new_password"].encode('utf-8'), bcrypt.gensalt(14)).decode('utf-8')
            cursor.execute(f"UPDATE {table} SET password = %s WHERE {id_field} = %s", (hashed, data["user_id"]))
            conn.commit()

        return jsonify({"message": "Mot de passe modifié avec succès."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

@auth_bp.route("/auth/2fa/disable", methods=["POST"])
def disable_2fa():
    """Désactive l'A2F pour l'utilisateur spécifié"""
    data = request.get_json()
    if not data or not all(k in data for k in ("user_id", "role")):
        return jsonify({"error": "Champs user_id et role requis"}), 400
        
    table = "Teacher" if data["role"] in ["teacher", "admin"] else "Student"
    id_field = "teacher_id" if table == "Teacher" else "student_id"

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            query = f"UPDATE {table} SET totp_secret = NULL WHERE {id_field} = %s"
            cursor.execute(query, (data["user_id"],))
            conn.commit()
        return jsonify({"message": "A2F désactivée avec succès."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

