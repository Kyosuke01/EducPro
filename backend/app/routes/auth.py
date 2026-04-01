"""
routes/auth.py — Routes d'authentification et de profils (étudiants/professeurs).

Endpoints :
    POST /api/auth/login              — Connexion unifiée (étudiant ou professeur/admin)
    GET  /api/students                — Liste de tous les étudiants
    GET  /api/students/<int:id>       — Infos d'un étudiant
    GET  /api/teachers                — Liste de tous les professeurs
    GET  /api/teachers/<int:id>       — Infos d'un professeur
"""

from flask import Blueprint, request, jsonify, current_app
from app.db import get_db_connection
import bcrypt
import pyotp
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

auth_bp = Blueprint("auth", __name__)


def _format_user_payload(record, role):
    payload = {
        "id": record["student_id"] if role == "student" else record["teacher_id"],
        "first_name": record["first_name"],
        "last_name": record["last_name"],
        "role": role,
        "has_2fa": bool(record.get("totp_secret"))
    }

    if role == "student":
        payload["email"] = record["mail_student"]
        payload["class_name"] = record.get("class_name")
    else:
        payload["email"] = record["mail_teacher"]
        payload["topic_name"] = record.get("topic_name")

    return payload


def _login_success_response(payload):
    return jsonify({
        "message": "Connexion réussie.",
        "user": payload
    }), 200


def _get_2fa_serializer():
    secret = current_app.config.get("SECRET_KEY")
    return URLSafeTimedSerializer(secret, salt="login-2fa")


def _issue_pending_token(user_id, role):
    return _get_2fa_serializer().dumps({"user_id": user_id, "role": role})


def _process_login_for_user(record, role, code):
    user_payload = _format_user_payload(record, role)
    totp_secret = record.get("totp_secret")

    if not totp_secret:
        return _login_success_response(user_payload)

    if code:
        if not pyotp.TOTP(totp_secret).verify(code):
            return jsonify({"error": "Code 2FA invalide"}), 401
        return _login_success_response(user_payload)

    pending_token = _issue_pending_token(user_payload["id"], role)
    return jsonify({
        "message": "Code 2FA requis",
        "require_2fa": True,
        "pending_token": pending_token,
        "user": user_payload
    }), 202


def _load_pending_token(token):
    serializer = _get_2fa_serializer()
    return serializer.loads(token, max_age=300)


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
    code = data.get("code")

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
                return _process_login_for_user(student, "student", code)

            # 2) Chercher dans Teacher
            cursor.execute(
                "SELECT teacher_id, first_name, last_name, mail_teacher, is_admin, topic_name, password, totp_secret "
                "FROM Teacher WHERE mail_teacher = %s",
                (email,)
            )
            teacher = cursor.fetchone()

            if teacher and bcrypt.checkpw(password.encode('utf-8'), teacher["password"].encode('utf-8')):
                role = "admin" if teacher.get("is_admin") else "teacher"
                return _process_login_for_user(teacher, role, code)

            # Aucun match ou mauvais mot de passe
            return jsonify({"error": "Email ou mot de passe incorrect."}), 401

    except Exception as e:
        return jsonify({"error": f"Erreur serveur : {str(e)}"}), 500
    finally:
        if conn:
            conn.close()


@auth_bp.route("/auth/login/2fa", methods=["POST"])
def finalize_login_2fa():
    """Valide un défi 2FA déclenché après l'étape mot de passe."""
    data = request.get_json() or {}
    token = data.get("token")
    code = data.get("code")

    if not token or not code:
        return jsonify({"error": "Les champs 'token' et 'code' sont requis."}), 400

    try:
        pending = _load_pending_token(token)
    except SignatureExpired:
        return jsonify({"error": "Le défi 2FA a expiré. Veuillez recommencer."}), 401
    except BadSignature:
        return jsonify({"error": "Jeton 2FA invalide."}), 401

    user_id = pending.get("user_id")
    role = pending.get("role")

    if not user_id or role not in {"student", "teacher", "admin"}:
        return jsonify({"error": "Jeton 2FA invalide."}), 401

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            if role == "student":
                cursor.execute(
                    "SELECT student_id, first_name, last_name, mail_student, class_name, totp_secret "
                    "FROM Student WHERE student_id = %s",
                    (user_id,)
                )
            else:
                cursor.execute(
                    "SELECT teacher_id, first_name, last_name, mail_teacher, is_admin, topic_name, totp_secret "
                    "FROM Teacher WHERE teacher_id = %s",
                    (user_id,)
                )
            user = cursor.fetchone()

        if not user or not user.get("totp_secret"):
            return jsonify({"error": "Utilisateur introuvable ou A2F désactivée."}), 404

        if not pyotp.TOTP(user["totp_secret"]).verify(code):
            return jsonify({"error": "Code 2FA invalide"}), 401

        if role == "student":
            final_role = "student"
        else:
            final_role = "admin" if user.get("is_admin") else "teacher"

        return _login_success_response(_format_user_payload(user, final_role))
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
        if conn:
            conn.close()


@auth_bp.route("/auth/forgot-password", methods=["POST"])
def forgot_password():
    """
    Recherche l'email dans Student ou Teacher.
    Vérifie si totp_secret existe.
    Body JSON : { "email": "..." }
    """
    data = request.get_json()
    email = data.get("email")
    if not email:
        return jsonify({"error": "Email requis"}), 400

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Chercher dans Student
            cursor.execute(
                "SELECT student_id as id, 'student' as role, totp_secret FROM Student WHERE mail_student = %s", (email,))
            user = cursor.fetchone()
            if not user:
                cursor.execute(
                    "SELECT teacher_id as id, 'teacher' as role, totp_secret FROM Teacher WHERE mail_teacher = %s", (email,))
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
        if conn:
            conn.close()


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
            cursor.execute(
                "SELECT student_id as id, 'Student' as tbl, totp_secret FROM Student WHERE mail_student = %s", (email,))
            user = cursor.fetchone()
            id_field = "student_id"
            if not user:
                cursor.execute(
                    "SELECT teacher_id as id, 'Teacher' as tbl, totp_secret FROM Teacher WHERE mail_teacher = %s", (email,))
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
        if conn:
            conn.close()


@auth_bp.route("/users/change-password", methods=["POST"])
def change_password():
    """
    Changement classique du MDP via paramètres.
    Body JSON : { "user_id": 1, "role": "student/teacher/admin", "old_password": "...", "new_password": "..." }
    """
    data = request.get_json()
    if not all(k in data for k in ("user_id", "role", "old_password", "new_password")):
        return jsonify({"error": "user_id, role, old_password, new_password requis"}), 400

    code = data.get("code")

    table = "Teacher" if data["role"] in ["teacher", "admin"] else "Student"
    id_field = "teacher_id" if table == "Teacher" else "student_id"

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT password, totp_secret FROM {table} WHERE {id_field} = %s", (data["user_id"],))
            user = cursor.fetchone()

            if not user or not bcrypt.checkpw(data["old_password"].encode('utf-8'), user["password"].encode('utf-8')):
                return jsonify({"error": "Ancien mot de passe incorrect"}), 400

            # Si A2F activée, valider le code fourni
            if user.get("totp_secret"):
                if not code:
                    return jsonify({"error": "Code 2FA requis"}), 401
                if not pyotp.TOTP(user["totp_secret"]).verify(code):
                    return jsonify({"error": "Code 2FA invalide"}), 401

            hashed = bcrypt.hashpw(data["new_password"].encode('utf-8'), bcrypt.gensalt(14)).decode('utf-8')
            cursor.execute(f"UPDATE {table} SET password = %s WHERE {id_field} = %s", (hashed, data["user_id"]))
            conn.commit()

        return jsonify({"message": "Mot de passe modifié avec succès."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()


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
        if conn:
            conn.close()
