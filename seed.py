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
ROOM_NAMES = [f"Salle {i}" for i in range(101, 115)] + ["Labo 1", "Labo 2", "Gymnase", "Amphi A"]

# Créneaux horaires classiques (Début, Durée en heures)
TIME_SLOTS = [8, 9, 10, 11, 13, 14, 15, 16]

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(14)).decode('utf-8')

def run_seed():
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            print("--- NETTOYAGE ET RÉINITIALISATION ---")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            for table in ["SupportMessage", "SupportTicket", "ATTENDANCE", "EDT", "Grade", "Topic", "Student", "Class", "Teacher", "Room"]:
                cursor.execute(f"TRUNCATE TABLE {table}")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

            hashed_pwd = hash_password(TEST_PASSWORD)

            # 1. SALLES
            for r in ROOM_NAMES:
                cursor.execute("INSERT INTO Room (name) VALUES (%s)", (r,))

            # 2. PROFESSEURS (Admin + Prof Test + 23 Aléatoires)
            print("[1/6] Création des 25 professeurs...")
            cursor.execute("INSERT INTO Teacher (first_name, last_name, mail_teacher, password, is_admin) VALUES (%s, %s, %s, %s, %s)",
                           ("Admin", "System", "admin_test@educpro.com", hashed_pwd, 1))
            
            cursor.execute("INSERT INTO Teacher (first_name, last_name, mail_teacher, password, is_admin, topic_name) VALUES (%s, %s, %s, %s, %s, %s)",
                           ("Prof", "Test", "teacher_test@educpro.com", hashed_pwd, 0, "Mathématiques"))

            fn_list = ["Marc", "Sophie", "Jean", "Claire", "Luc", "Marie", "Antoine", "Julie", "Thomas", "Lea", "Yanis", "Emma"]
            ln_list = ["Durand", "Leroy", "Moreau", "Simon", "Michel", "Garcia", "Bertrand", "Roux", "David", "Petit", "Muller"]
            
            teachers = []
            teacher_counter = 1
            for i in range(NB_TEACHERS - 1):
                fn, ln = random.choice(fn_list), random.choice(ln_list)
                email = f"{fn.lower()}.{ln.lower()}{teacher_counter:04d}@educpro.com"
                teacher_counter += 1
                cursor.execute("INSERT INTO Teacher (first_name, last_name, mail_teacher, password, is_admin, topic_name) VALUES (%s, %s, %s, %s, %s, %s)",
                               (fn, ln, email, hashed_pwd, 0, random.choice(TOPICS_LIST)))
                teachers.append({'id': cursor.lastrowid, 'fname': fn, 'lname': ln})

            # 3. CLASSES ET ÉTUDIANTS
            print(f"[2/6] Création des classes et de {NB_STUDENTS} étudiants...")
            for name in CLASS_NAMES:
                cursor.execute("INSERT INTO Class (name, max_capacity, homeroom_teacher_id) VALUES (%s, %s, %s)", 
                               (name, 35, random.choice(teachers)['id']))

            cursor.execute("INSERT INTO Student (first_name, last_name, mail_student, password, class_name, dob) VALUES (%s, %s, %s, %s, %s, %s)",
                           ("Etudiant", "Test", "student_test@edu.com", hashed_pwd, CLASS_NAMES[0], "2007-05-15"))

            student_counter = 1
            for i in range(NB_STUDENTS - 1):
                fn, ln = random.choice(fn_list), random.choice(ln_list)
                email = f"{fn.lower()}.{ln.lower()}{student_counter:04d}@edu.com"
                student_counter += 1
                dob = f"{random.randint(2006, 2010)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
                cursor.execute("INSERT INTO Student (first_name, last_name, mail_student, password, class_name, dob) VALUES (%s, %s, %s, %s, %s, %s)",
                               (fn, ln, email, hashed_pwd, random.choice(CLASS_NAMES), dob))

            # 4. MATIÈRES PAR CLASSE
            print("[3/6] Attribution des matières (Topics) par classe...")
            topics_by_class = {}
            for cl_name in CLASS_NAMES:
                cursor.execute("SELECT class_id FROM Class WHERE name = %s", (cl_name,))
                c_id = cursor.fetchone()['class_id']
                topics_by_class[cl_name] = []
                
                # Chaque classe a 6 à 8 matières
                class_selection = random.sample(TOPICS_LIST, random.randint(6, 8))
                for t_name in class_selection:
                    prof = random.choice(teachers)
                    unique_t_name = f"{t_name} ({cl_name})"
                    cursor.execute("INSERT INTO Topic (name, teacher_id, class_id) VALUES (%s, %s, %s)", 
                                   (unique_t_name, prof['id'], c_id))
                    topics_by_class[cl_name].append({'name': unique_t_name, 'prof': prof})

            # 5. EMPLOI DU TEMPS RÉALISTE ET VARIÉ
            print("[4/6] Génération des emplois du temps (EDT) variés...")
            # On génère sur 5 jours (Lundi à Vendredi) de la semaine courante
            today = datetime.now()
            start_of_week = today - timedelta(days=today.weekday()) 

            for cl_name in CLASS_NAMES:
                for day_idx in range(5): # 0=Lundi, 4=Vendredi
                    current_day = start_of_week + timedelta(days=day_idx)
                    
                    # On mélange les créneaux et on en choisit un nombre aléatoire (ex: 5 à 7 cours par jour)
                    daily_slots = random.sample(TIME_SLOTS, random.randint(5, 7))
                    daily_slots.sort()

                    skip_next = False
                    for i, hour in enumerate(daily_slots):
                        if skip_next:
                            skip_next = False
                            continue
                        
                        start_time = current_day.replace(hour=hour, minute=0, second=0, microsecond=0)
                        
                        # Aléatoire : cours de 1h ou 2h (si le créneau suivant est libre)
                        duration = 1
                        if i + 1 < len(daily_slots) and daily_slots[i+1] == hour + 1 and random.random() > 0.5:
                            duration = 2
                            skip_next = True
                        
                        end_time = start_time + timedelta(hours=duration)
                        topic_info = random.choice(topics_by_class[cl_name])
                        
                        cursor.execute("""
                            INSERT INTO EDT (class_name, teacher_f_name, teacher_l_name, topic_name, room_name, start_time, end_time)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (cl_name, topic_info['prof']['fname'], topic_info['prof']['lname'], 
                              topic_info['name'], random.choice(ROOM_NAMES), start_time, end_time))

            # 6. NOTES, ABSENCES ET TICKETS
            print("[5/6] Génération des notes et absences...")
            cursor.execute("SELECT student_id, class_name FROM Student")
            students = cursor.fetchall()
            for s in students:
                # 5 notes par élève
                for _ in range(5):
                    t_name = random.choice(topics_by_class[s['class_name']])['name']
                    cursor.execute("INSERT INTO Grade (grade, student_id, topic_name) VALUES (%s, %s, %s)", 
                                   (round(random.uniform(5, 20), 1), s['student_id'], t_name))

            # Absences
            cursor.execute("SELECT edt_id FROM EDT ORDER BY RAND() LIMIT 60")
            for row in cursor.fetchall():
                cursor.execute("INSERT INTO ATTENDANCE (student_id, edt_id, date_attendance, status, justified) VALUES (%s, %s, %s, %s, %s)",
                               (random.choice(students)['student_id'], row['edt_id'], today.date(), random.choice(['absent', 'late']), random.choice([0, 1])))

            print("[6/6] Finalisation...")
            conn.commit()
            
            print("\n" + "★"*40)
            print("  BASE DE DONNÉES PEUPLÉE AVEC SUCCÈS")
            print("  - Admin   : admin_test@educpro.com")
            print("  - Prof    : teacher_test@educpro.com")
            print("  - Student : student_test@edu.com")
            print(f"  - Password: {TEST_PASSWORD}")
            print("★"*40)

    except Exception as e:
        print(f"\n[ERREUR] : {e}")
        if conn: conn.rollback()
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    run_seed()