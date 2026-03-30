from flask import Blueprint, jsonify, request
from app.db import get_db_connection
import bcrypt

users_bp = Blueprint("users", __name__)

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
                users.append({"username": f"{s['first_name']} {s['last_name']}", "email": s['email'], "role": s['role']})
            for t in teachers:
                users.append({"username": f"{t['first_name']} {t['last_name']}", "email": t['email'], "role": t['role']})
                
        return jsonify(users), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

# POST créer un utilisateur (Sécurisé par accès Admin)
@users_bp.route("/", methods=["POST"])
def create_user():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Données invalides."}), 400
        
    user_type = data.get("user_type")
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    email = data.get("email")
    password = data.get("password")
    
    if not all([user_type, first_name, last_name, email, password]):
        return jsonify({"error": "Tous les champs (nom, prénom, email, mot de passe) sont requis."}), 400
        
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(14)).decode('utf-8')
    
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            if user_type == "student":
                class_name = data.get("class_name")
                if not class_name:
                    return jsonify({"error": "La classe est requise pour un étudiant."}), 400
                
                cursor.execute(
                    "INSERT INTO Student (first_name, last_name, mail_student, password, class_name) VALUES (%s, %s, %s, %s, %s)",
                    (first_name, last_name, email, hashed_password, class_name)
                )
            elif user_type == "teacher":
                topic_name = data.get("topic_name")
                if not topic_name:
                    return jsonify({"error": "La matière est requise pour un professeur."}), 400
                    
                cursor.execute(
                    "INSERT INTO Teacher (first_name, last_name, mail_teacher, password, topic_name, is_admin) VALUES (%s, %s, %s, %s, %s, 0)",
                    (first_name, last_name, email, hashed_password, topic_name)
                )
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
                cursor.execute(
                    "UPDATE Student SET first_name=%s, last_name=%s, mail_student=%s, class_name=%s WHERE student_id=%s",
                    (first_name, last_name, email, class_name, user_id)
                )
            elif user_type == "teacher":
                topic_name = data.get("topic_name")
                cursor.execute(
                    "UPDATE Teacher SET first_name=%s, last_name=%s, mail_teacher=%s, topic_name=%s WHERE teacher_id=%s",
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