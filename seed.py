import sys
import os
import bcrypt
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Configuration de l'environnement
load_dotenv(os.path.join(os.path.dirname(__file__), 'backend', '.env'))

if os.getenv("DB_HOST") == "db" or not os.getenv("DB_HOST"):
    os.environ["DB_HOST"] = "127.0.0.1"

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
from app.db import get_db_connection

# ============================================
# CONFIGURATION ET CONSTANTES
# ============================================
TEST_PASSWORD = "Test1234!"
NB_STUDENTS = 210  
NB_TEACHERS = 25   
TOPICS_LIST = [
    "Mathématiques", "Français", "Histoire-Géo", "Anglais", 
    "Physique-Chimie", "SVT", "Philosophie", "Arts Plastiques", 
    "Éducation Physique", "Informatique", "Espagnol", "SES"
]
CLASS_NAMES = ["2nde A", "2nde B", "1ère S-A", "1ère S-B", "1ère STMG", "Terminale S", "Terminale L"]
ROOM_NAMES = [f"Salle {i}" for i in range(101, 110)] + ["Labo 1", "Labo 2", "Gymnase", "Amphi A"]

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(14)).decode('utf-8')

def run_seed():
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            print("--- NETTOYAGE DES ANCIENNES DONNÉES ---")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            tables = ["SupportMessage", "SupportTicket", "ATTENDANCE", "EDT", "Grade", "Topic", "Student", "Class", "Teacher", "Room"]
            for table in tables:
                cursor.execute(f"TRUNCATE TABLE {table}")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

            print(f"\n[INFO] Mot de passe commun : {TEST_PASSWORD}")
            hashed_pwd = hash_password(TEST_PASSWORD)

            # 1. SALLES
            print("[1/9] Création des salles...")
            for r in ROOM_NAMES:
                cursor.execute("INSERT INTO Room (name) VALUES (%s)", (r,))

            # 2. PROFESSEURS
            print("[2/9] Création des professeurs...")
            # Admin de test
            cursor.execute("""
                INSERT INTO Teacher (first_name, last_name, mail_teacher, password, is_admin)
                VALUES (%s, %s, %s, %s, %s)
            """, ("Admin", "System", "admin_test@educpro.com", hashed_pwd, 1))

            # Prof de test
            cursor.execute("""
                INSERT INTO Teacher (first_name, last_name, mail_teacher, password, is_admin, topic_name)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, ("Prof", "Test", "teacher_test@educpro.com", hashed_pwd, 0, "Mathématiques"))

            teachers_data = []
            fn_list = ["Marc", "Sophie", "Jean", "Claire", "Luc", "Marie", "Antoine", "Julie", "Thomas", "Lea"]
            ln_list = ["Durand", "Leroy", "Moreau", "Simon", "Michel", "Garcia", "Bertrand", "Roux", "David", "Petit"]
            
            for i in range(NB_TEACHERS - 1):
                fn, ln = random.choice(fn_list), random.choice(ln_list)
                email = f"{fn.lower()}.{ln.lower()}{random.randint(1000,9999)}@educpro.com"
                cursor.execute("""
                    INSERT INTO Teacher (first_name, last_name, mail_teacher, password, is_admin, topic_name)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (fn, ln, email, hashed_pwd, 0, random.choice(TOPICS_LIST)))
                teachers_data.append(cursor.lastrowid)

            # 3. CLASSES
            print("[3/9] Création des classes...")
            for name in CLASS_NAMES:
                hp_id = random.choice(teachers_data)
                cursor.execute("INSERT INTO Class (name, max_capacity, homeroom_teacher_id) VALUES (%s, %s, %s)", 
                               (name, 35, hp_id))

            # 4. ÉTUDIANTS
            print(f"[4/9] Création des étudiants ({NB_STUDENTS})...")
            cursor.execute("""
                INSERT INTO Student (first_name, last_name, mail_student, password, class_name, dob)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, ("Etudiant", "Test", "student_test@edu.com", hashed_pwd, CLASS_NAMES[0], "2007-05-15"))

            for i in range(NB_STUDENTS - 1):
                fn, ln = random.choice(fn_list), random.choice(ln_list)
                email = f"{fn.lower()}.{ln.lower()}{random.randint(1000,9999)}@edu.com"
                cl = random.choice(CLASS_NAMES)
                dob = f"{random.randint(2006, 2010)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
                cursor.execute("""
                    INSERT INTO Student (first_name, last_name, mail_student, password, class_name, dob)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (fn, ln, email, hashed_pwd, cl, dob))

            # 5. MATIÈRES (Correction de l'erreur Duplicate Entry)
            print("[5/9] Liaison professeurs / matières / classes...")
            inserted_topics = []
            for cl_name in CLASS_NAMES:
                cursor.execute("SELECT class_id FROM Class WHERE name = %s", (cl_name,))
                c_id = cursor.fetchone()['class_id']
                
                # On prend 5 matières au hasard pour cette classe
                sampled_topics = random.sample(TOPICS_LIST, 5)
                for t_base_name in sampled_topics:
                    t_id = random.choice(teachers_data)
                    # On rend le nom unique pour la table Topic : "Maths - 2nde A"
                    unique_name = f"{t_base_name} ({cl_name})"
                    cursor.execute("INSERT INTO Topic (name, teacher_id, class_id) VALUES (%s, %s, %s)", 
                                   (unique_name, t_id, c_id))
                    inserted_topics.append(unique_name)

            # 6. EMPLOI DU TEMPS
            print("[6/9] Génération des EDT...")
            base_date = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
            for cl_name in CLASS_NAMES:
                # Récupérer les matières de CETTE classe uniquement
                cursor.execute("SELECT name FROM Topic WHERE name LIKE %s", (f"%({cl_name})",))
                class_topics = [row['name'] for row in cursor.fetchall()]
                
                for day in range(5):
                    for hour in [8, 10, 14, 16]:
                        start = base_date + timedelta(days=day, hours=hour)
                        # On récupère un prof au hasard
                        cursor.execute("SELECT first_name, last_name FROM Teacher WHERE is_admin=0 ORDER BY RAND() LIMIT 1")
                        t = cursor.fetchone()
                        
                        cursor.execute("""
                            INSERT INTO EDT (class_name, teacher_f_name, teacher_l_name, topic_name, room_name, start_time, end_time)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (cl_name, t['first_name'], t['last_name'], random.choice(class_topics), random.choice(ROOM_NAMES), start, start + timedelta(hours=2)))

            # 7. NOTES
            print("[7/9] Attribution des notes...")
            cursor.execute("SELECT student_id, class_name FROM Student")
            all_students = cursor.fetchall()
            for s in all_students:
                # On récupère les matières de sa classe
                cursor.execute("SELECT name FROM Topic WHERE name LIKE %s", (f"%({s['class_name']})",))
                available_topics = [row['name'] for row in cursor.fetchall()]
                if available_topics:
                    for _ in range(3):
                        cursor.execute("INSERT INTO Grade (grade, student_id, topic_name) VALUES (%s, %s, %s)", 
                                       (round(random.uniform(7, 19), 1), s['student_id'], random.choice(available_topics)))

            # 8. PRÉSENCES
            print("[8/9] Génération des absences...")
            cursor.execute("SELECT edt_id FROM EDT LIMIT 100")
            edts = [e['edt_id'] for e in cursor.fetchall()]
            cursor.execute("SELECT student_id FROM Student")
            st_ids = [s['student_id'] for s in cursor.fetchall()]
            for _ in range(40):
                cursor.execute("""
                    INSERT INTO ATTENDANCE (student_id, edt_id, date_attendance, status, justified)
                    VALUES (%s, %s, %s, %s, %s)
                """, (random.choice(st_ids), random.choice(edts), datetime.now().date(), random.choice(['absent', 'late']), random.choice([0, 1])))

            # 9. TICKETS
            print("[9/9] Création de tickets...")
            for _ in range(5):
                sid = random.choice(st_ids)
                cursor.execute("INSERT INTO SupportTicket (subject, student_id, created_by_role, created_by_id) VALUES (%s, %s, %s, %s)", 
                               ("Besoin d'aide EDT", sid, 'student', sid))

            conn.commit()
            print("\n" + "="*50)
            print("MEGA SEED RÉUSSI !")
            print(f"Admin   : admin_test@educpro.com")
            print(f"Prof    : teacher_test@educpro.com")
            print(f"Student : student_test@edu.com")
            print(f"MDP     : {TEST_PASSWORD}")
            print("="*50)

    except Exception as e:
        print(f"\n[ERREUR] : {e}")
        if conn: conn.rollback()
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    run_seed()