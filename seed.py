import sys
import os
import bcrypt
import random
from dotenv import load_dotenv

# Charger explicitement le .env du backend pour avoir les identifiants
load_dotenv(os.path.join(os.path.dirname(__file__), 'backend', '.env'))

# Si executé en local (hors Docker), le host 'db' défini dans .env ne marchera pas.
# On force l'hôte sur localhost (127.0.0.1)
if os.getenv("DB_HOST") == "db" or not os.getenv("DB_HOST"):
    os.environ["DB_HOST"] = "127.0.0.1"

# Ajouter le dossier backend au path pour pouvoir importer les modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.db import get_db_connection

def hash_password(password):
    """
    Règle de sécurité stricte : Hachage du mot de passe avec bcrypt (cost=14)
    comme défini dans vos routes d'authentification existantes.
    """
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(14)).decode('utf-8')

def run_seed():
    """
    Vérifie l'existence des utilisateurs de test et peuple la base si nécessaire.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 1. Vérification : Le seed a-t-il déjà été exécuté ? (On check l'admin de test)
            cursor.execute("SELECT teacher_id FROM Teacher WHERE mail_teacher = 'admin_test@educpro.com'")
            if cursor.fetchone():
                print("[SEED] Utilisateurs de test déjà présents. Seed ignoré pour ne pas écraser les données.")
                return

            print("[SEED] Initialisation de la base de données : création des utilisateurs de test et factices...")

            # Définir le mot de passe de test commun
            test_password = hash_password("Test1234!")

            # 2. Création des COMPTES DE TEST GARANTIS (Admin, Prof, Etudiant)
            # Admin
            cursor.execute("""
                INSERT INTO Teacher (first_name, last_name, mail_teacher, password, is_admin, topic_name)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, ("Admin", "Test", "admin_test@educpro.com", test_password, 1, None))

            # Professeur
            cursor.execute("""
                INSERT INTO Teacher (first_name, last_name, mail_teacher, password, is_admin, topic_name)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, ("Prof", "Test", "prof_test@educpro.com", test_password, 0, "Informatique"))
            
            # Obtenir une classe par défaut pour l'étudiant
            cursor.execute("SELECT name FROM Class LIMIT 1")
            class_row = cursor.fetchone()
            if class_row:
                default_class = class_row['name']
            else:
                cursor.execute("INSERT INTO Class (name, max_capacity) VALUES ('Classe Test', 35)")
                default_class = 'Classe Test'

            # Etudiant
            cursor.execute("""
                INSERT INTO Student (first_name, last_name, mail_student, password, class_name, dob)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, ("Etudiant", "Test", "student_test@educpro.com", test_password, default_class, "2005-01-01"))


            # 3. Création d'utilisateurs factices aléatoires pour peupler la BD
            first_names = ["Lucas", "Sarah", "Mohamed", "Julie", "Kevin", "Léa", "Thomas", "Marie", "Hugo", "Camille"]
            last_names = ["Martin", "Bernard", "Dubois", "Thomas", "Robert", "Richard", "Petit", "Durand", "Leroy", "Moreau"]
            topics = ["Mathématiques", "Français", "Histoire-Géo", "Anglais", "Physique", "SVT"]
            
            # Géneration de 5 profs aléatoires
            for _ in range(5):
                fn = random.choice(first_names)
                ln = random.choice(last_names)
                email = f"{fn.lower()}.{ln.lower()}{random.randint(100,999)}@educpro.com"
                topic = random.choice(topics)
                cursor.execute("""
                    INSERT INTO Teacher (first_name, last_name, mail_teacher, password, is_admin, topic_name)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (fn, ln, email, test_password, 0, topic))
                
            # Géneration de 15 étudiants aléatoires
            for _ in range(15):
                fn = random.choice(first_names)
                ln = random.choice(last_names)
                email = f"{fn.lower()}.{ln.lower()}{random.randint(100,999)}@edu.com"
                # Année de naissance random pour un lycéen
                year = random.randint(2005, 2009)
                month = random.randint(1, 12)
                day = random.randint(1, 28)
                dob = f"{year}-{month:02d}-{day:02d}"
                cursor.execute("""
                    INSERT INTO Student (first_name, last_name, mail_student, password, class_name, dob)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (fn, ln, email, test_password, default_class, dob))

            conn.commit()
            print("[SEED] Terminé avec succès ! (Utilisateurs factices et comptes de tests insérés)")

    except Exception as e:
        print(f"[SEED ERROR] Erreur lors de l'initialisation : {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    run_seed()
