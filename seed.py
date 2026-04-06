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
NB_TEACHERS = 26
TOPICS_LIST = [
    "Mathématiques", "Français", "Histoire-Géo", "Anglais", 
    "Physique-Chimie", "SVT", "Philosophie", "Arts Plastiques", 
    "Éducation Physique", "Informatique", "Espagnol", "SES"
]
CLASS_NAMES = ["2nde A", "2nde B", "1ère S-A", "1ère S-B", "1ère STMG", "Terminale S", "Terminale L"]
ROOM_NAMES = [f"Salle {i}" for i in range(101, 115)] + ["Labo 1", "Labo 2", "Gymnase A", "Gymnase B", "Amphi A"]

# Créneaux horaires classiques (Début, Durée en heures)
TIME_SLOTS = [8, 9, 10, 11, 13, 14, 15, 16]
DAYS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
SPECIALIZED_ROOM_BY_TOPIC = {
    "Éducation Physique": ["Gymnase A", "Gymnase B"],
    "Informatique": ["Labo 1", "Labo 2"],
    "Physique-Chimie": ["Labo 1", "Labo 2"],
    "SVT": ["Labo 1", "Labo 2"],
    "Arts Plastiques": ["Amphi A", "Salle 114"]
}
STRICT_SPECIALIZED_TOPICS = {"Éducation Physique", "Informatique"}

# Modèle d'EDT réaliste inspiré de emploi_du_temps_final.xlsx
# Chaque ligne = [08-09, 09-10, 10-11, 11-12, 13-14, 14-15, 15-16, 16-17]
WEEKLY_EDT_TEMPLATE = {
    "2nde A": [
        ["Mathématiques", "Mathématiques", "Français", "Français", "Anglais", "Anglais", "Histoire-Géo", "Éducation Physique"],
        ["Physique-Chimie", "Physique-Chimie", "SVT", "SVT", "Français", "Mathématiques", "Espagnol", "Espagnol"],
        ["Histoire-Géo", "Histoire-Géo", "Mathématiques", "Informatique", None, None, None, None],
        ["Français", "Français", "Anglais", "Mathématiques", "Physique-Chimie", "SES", "SES", "Arts Plastiques"],
        ["SVT", "Mathématiques", "Philosophie", "Philosophie", "Éducation Physique", "Informatique", None, None],
    ],
    "2nde B": [
        ["Français", "Français", "Mathématiques", "Mathématiques", "Anglais", "Histoire-Géo", "SES", "Éducation Physique"],
        ["SVT", "SVT", "Physique-Chimie", "Physique-Chimie", "Mathématiques", "Français", "Espagnol", "Espagnol"],
        ["Mathématiques", "Histoire-Géo", "Informatique", None, None, None, None, None],
        ["Anglais", "Anglais", "Français", "SES", "Physique-Chimie", "Mathématiques", "Arts Plastiques", None],
        ["Mathématiques", "SVT", "Philosophie", "Philosophie", "Éducation Physique", "Informatique", None, None],
    ],
    "1ère S-A": [
        ["Mathématiques", "Mathématiques", "Physique-Chimie", "Physique-Chimie", "SVT", "SVT", "Anglais", None],
        ["Français", "Français", "Histoire-Géo", "Histoire-Géo", "Mathématiques", "Mathématiques", "Informatique", None],
        ["Physique-Chimie", "SVT", "Mathématiques", None, None, None, None, None],
        ["Anglais", "Français", "Mathématiques", "Physique-Chimie", "Éducation Physique", "Éducation Physique", None, None],
        ["Histoire-Géo", "Philosophie", "Philosophie", "SVT", "Informatique", None, None, None],
    ],
    "1ère S-B": [
        ["Physique-Chimie", "Mathématiques", "Mathématiques", "SVT", "SVT", "Anglais", "Français", None],
        ["Français", "Histoire-Géo", "Histoire-Géo", "Mathématiques", "Mathématiques", "Informatique", None, None],
        ["Mathématiques", "SVT", "Physique-Chimie", None, None, None, None, None],
        ["Anglais", "Français", "Mathématiques", "Physique-Chimie", "Éducation Physique", "Éducation Physique", None, None],
        ["Histoire-Géo", "Philosophie", "Philosophie", "SVT", "Informatique", None, None, None],
    ],
    "1ère STMG": [
        ["SES", "SES", "Mathématiques", "Français", "Anglais", "Histoire-Géo", None, None],
        ["SES", "Mathématiques", "Mathématiques", "Français", "Français", "Éducation Physique", None, None],
        ["SES", "Mathématiques", "Informatique", None, None, None, None, None],
        ["Français", "Anglais", "Histoire-Géo", "SES", "Éducation Physique", None, None, None],
        ["Mathématiques", "SES", "Philosophie", "Philosophie", "Informatique", None, None, None],
    ],
    "Terminale S": [
        ["Mathématiques", "Physique-Chimie", "Physique-Chimie", "SVT", "SVT", "Philosophie", "Anglais", None],
        ["Philosophie", "Mathématiques", "Mathématiques", "Anglais", "Histoire-Géo", None, None, None],
        ["Physique-Chimie", "SVT", "Mathématiques", None, None, None, None, None],
        ["Anglais", "Mathématiques", "Physique-Chimie", "Éducation Physique", "Éducation Physique", None, None, None],
        ["Histoire-Géo", "Informatique", "SVT", "Philosophie", None, None, None, None],
    ],
    "Terminale L": [
        ["Philosophie", "Français", "Français", "Anglais", "Histoire-Géo", None, None, None],
        ["Français", "Philosophie", "Philosophie", "Espagnol", "Espagnol", None, None, None],
        ["Histoire-Géo", "Anglais", "Informatique", None, None, None, None, None],
        ["Philosophie", "Français", "Histoire-Géo", "Arts Plastiques", "Éducation Physique", None, None, None],
        ["Anglais", "Espagnol", "Philosophie", "Informatique", None, None, None, None],
    ],
}

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

            # 2. PROFESSEURS (Admin + Prof Test + aléatoires)
            print(f"[1/6] Création des {NB_TEACHERS} professeurs...")
            cursor.execute("INSERT INTO Teacher (first_name, last_name, mail_teacher, password, is_admin) VALUES (%s, %s, %s, %s, %s)",
                           ("Admin", "System", "admin_test@educpro.com", hashed_pwd, 1))
            
            cursor.execute("INSERT INTO Teacher (first_name, last_name, mail_teacher, password, is_admin, topic_name) VALUES (%s, %s, %s, %s, %s, %s)",
                           ("Prof", "Test", "teacher_test@educpro.com", hashed_pwd, 0, "Mathématiques"))
            prof_test = {
                'id': cursor.lastrowid,
                'fname': 'Prof',
                'lname': 'Test',
                'topic': 'Mathématiques'
            }

            fn_list = ["Marc", "Sophie", "Jean", "Claire", "Luc", "Marie", "Antoine", "Julie", "Thomas", "Lea", "Yanis", "Emma"]
            ln_list = ["Durand", "Leroy", "Moreau", "Simon", "Michel", "Garcia", "Bertrand", "Roux", "David", "Petit", "Muller"]
            
            teachers = []
            teacher_counter = 1
            # On retire 2 comptes déjà créés (Admin + Prof Test)
            for i in range(NB_TEACHERS - 2):
                fn, ln = random.choice(fn_list), random.choice(ln_list)
                email = f"{fn.lower()}.{ln.lower()}{teacher_counter:04d}@educpro.com"
                teacher_counter += 1
                assigned_topic = random.choice(TOPICS_LIST)
                cursor.execute("INSERT INTO Teacher (first_name, last_name, mail_teacher, password, is_admin, topic_name) VALUES (%s, %s, %s, %s, %s, %s)",
                               (fn, ln, email, hashed_pwd, 0, assigned_topic))
                teachers.append({'id': cursor.lastrowid, 'fname': fn, 'lname': ln, 'topic': assigned_topic})

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
            class_topic_map = {}
            prof_test_class = CLASS_NAMES[0]
            prof_test_topic_name = f"{prof_test['topic']} ({prof_test_class})"
            all_teachers_pool = [prof_test, *teachers]
            for cl_name in CLASS_NAMES:
                cursor.execute("SELECT class_id FROM Class WHERE name = %s", (cl_name,))
                c_id = cursor.fetchone()['class_id']
                topics_by_class[cl_name] = []
                class_topic_map[cl_name] = {}

                # Garantir un vrai périmètre pour Prof Test sur une classe cible.
                if cl_name == prof_test_class:
                    cursor.execute("INSERT INTO Topic (name, teacher_id, class_id) VALUES (%s, %s, %s)",
                                   (prof_test_topic_name, prof_test['id'], c_id))
                    prof_topic = {
                        'name': prof_test_topic_name,
                        'prof': {'id': prof_test['id'], 'fname': prof_test['fname'], 'lname': prof_test['lname']}
                    }
                    topics_by_class[cl_name].append(prof_topic)
                    class_topic_map[cl_name][prof_test['topic']] = prof_topic

                # Matières utilisées par classe selon le modèle réaliste.
                class_selection = sorted({
                    topic
                    for day in WEEKLY_EDT_TEMPLATE.get(cl_name, [])
                    for topic in day
                    if topic
                })

                for t_name in class_selection:
                    if cl_name == prof_test_class and t_name == prof_test['topic']:
                        continue

                    same_topic_teachers = [t for t in all_teachers_pool if t.get('topic') == t_name]
                    prof = random.choice(same_topic_teachers or all_teachers_pool)
                    unique_t_name = f"{t_name} ({cl_name})"
                    cursor.execute("INSERT INTO Topic (name, teacher_id, class_id) VALUES (%s, %s, %s)", 
                                   (unique_t_name, prof['id'], c_id))
                    topic_info = {'name': unique_t_name, 'prof': prof}
                    topics_by_class[cl_name].append(topic_info)
                    class_topic_map[cl_name][t_name] = topic_info

            # 5. EMPLOI DU TEMPS RÉALISTE (inspiré du fichier final, sans chevauchement)
            print("[4/6] Génération des emplois du temps réalistes...")
            # On génère sur 5 jours (Lundi à Vendredi) de la semaine courante
            today = datetime.now()
            start_of_week = today - timedelta(days=today.weekday()) 
            teacher_busy = set()  # (fname, lname, start_time)
            room_busy = set()     # (room_name, start_time)

            prof_test_allowed_slots = {
                start_of_week.replace(hour=8, minute=0, second=0, microsecond=0),                       # Lundi 08h (Math)
                (start_of_week + timedelta(days=1)).replace(hour=14, minute=0, second=0, microsecond=0),# Mardi 14h (Math)
                (start_of_week + timedelta(days=2)).replace(hour=10, minute=0, second=0, microsecond=0) # Mercredi 10h (Math)
            }

            for cl_name in CLASS_NAMES:
                class_template = WEEKLY_EDT_TEMPLATE.get(cl_name, [])
                for day_idx, day_slots in enumerate(class_template):
                    current_day = start_of_week + timedelta(days=day_idx)
                    for slot_idx, topic_base in enumerate(day_slots):
                        if not topic_base:
                            continue

                        start_hour = TIME_SLOTS[slot_idx]
                        start_time = current_day.replace(hour=start_hour, minute=0, second=0, microsecond=0)
                        end_time = start_time + timedelta(hours=1)

                        topic_info = class_topic_map.get(cl_name, {}).get(topic_base)
                        if not topic_info:
                            continue

                        same_topic_candidates = [t for t in all_teachers_pool if t.get('topic') == topic_base]
                        fallback_candidates = [t for t in all_teachers_pool if t.get('topic') != topic_base]
                        preferred_teacher = topic_info['prof']
                        teacher_candidates = [preferred_teacher, *same_topic_candidates, *fallback_candidates]

                        chosen_teacher = None
                        for candidate in teacher_candidates:
                            if not candidate:
                                continue
                            if cl_name == prof_test_class and topic_base == prof_test['topic']:
                                if candidate.get('id') == prof_test['id'] and start_time not in prof_test_allowed_slots:
                                    continue
                            teacher_key = (candidate['fname'], candidate['lname'], start_time)
                            if teacher_key in teacher_busy:
                                continue
                            chosen_teacher = candidate
                            break

                        if not chosen_teacher:
                            continue

                        preferred_rooms = SPECIALIZED_ROOM_BY_TOPIC.get(topic_base, [])[:]
                        fallback_rooms = [] if topic_base in STRICT_SPECIALIZED_TOPICS else [r for r in ROOM_NAMES if r not in preferred_rooms]
                        random.shuffle(preferred_rooms)
                        random.shuffle(fallback_rooms)
                        available_rooms = [*preferred_rooms, *fallback_rooms]
                        chosen_room = None
                        for room in available_rooms:
                            room_key = (room, start_time)
                            if room_key not in room_busy:
                                chosen_room = room
                                break
                        if not chosen_room:
                            continue

                        cursor.execute("""
                            INSERT INTO EDT (class_name, teacher_f_name, teacher_l_name, topic_name, room_name, start_time, end_time)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (
                            cl_name,
                            chosen_teacher['fname'],
                            chosen_teacher['lname'],
                            topic_info['name'],
                            chosen_room,
                            start_time,
                            end_time
                        ))

                        teacher_busy.add((chosen_teacher['fname'], chosen_teacher['lname'], start_time))
                        room_busy.add((chosen_room, start_time))

            # Nettoyage défensif: dédupliquer d'éventuels doublons exacts.
            cursor.execute("""
                DELETE e1 FROM EDT e1
                INNER JOIN EDT e2
                  ON e1.edt_id > e2.edt_id
                 AND e1.class_name = e2.class_name
                 AND e1.start_time = e2.start_time
                 AND e1.end_time = e2.end_time
            """)

            # Nettoyage défensif: supprimer tout chevauchement restant au niveau classe.
            cursor.execute("""
                DELETE e1 FROM EDT e1
                INNER JOIN EDT e2
                  ON e1.edt_id > e2.edt_id
                 AND e1.class_name = e2.class_name
                 AND e1.start_time < e2.end_time
                 AND e2.start_time < e1.end_time
            """)

            # Nettoyage défensif: supprimer tout chevauchement restant au niveau professeur.
            cursor.execute("""
                DELETE e1 FROM EDT e1
                INNER JOIN EDT e2
                  ON e1.edt_id > e2.edt_id
                 AND e1.teacher_f_name = e2.teacher_f_name
                 AND e1.teacher_l_name = e2.teacher_l_name
                 AND e1.start_time < e2.end_time
                 AND e2.start_time < e1.end_time
            """)

            # Nettoyage défensif: supprimer tout chevauchement restant au niveau salle.
            cursor.execute("""
                DELETE e1 FROM EDT e1
                INNER JOIN EDT e2
                  ON e1.edt_id > e2.edt_id
                 AND e1.room_name = e2.room_name
                 AND e1.start_time < e2.end_time
                 AND e2.start_time < e1.end_time
            """)

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

            # Fixture explicite : Prof Test évalue Etudiant Test + lui attribue une absence.
            cursor.execute(
                "SELECT student_id FROM Student WHERE mail_student = %s LIMIT 1",
                ("student_test@edu.com",)
            )
            student_test_row = cursor.fetchone()
            if student_test_row:
                student_test_id = student_test_row["student_id"]

                # Note explicite dans la matière de Prof Test.
                cursor.execute(
                    "INSERT INTO Grade (grade, student_id, topic_name) VALUES (%s, %s, %s)",
                    (14.5, student_test_id, prof_test_topic_name)
                )

                # Absence explicite sur un créneau de Prof Test.
                cursor.execute(
                    """
                    SELECT edt_id, start_time
                    FROM EDT
                    WHERE class_name = %s
                      AND teacher_f_name = %s
                      AND teacher_l_name = %s
                      AND topic_name = %s
                    ORDER BY start_time ASC
                    LIMIT 1
                    """,
                    (prof_test_class, prof_test['fname'], prof_test['lname'], prof_test_topic_name)
                )
                prof_test_edt_row = cursor.fetchone()
                if prof_test_edt_row:
                    cursor.execute(
                        "INSERT INTO ATTENDANCE (student_id, edt_id, date_attendance, status, justified) VALUES (%s, %s, %s, %s, %s)",
                        (student_test_id, prof_test_edt_row["edt_id"], today.date(), "absent", 0)
                    )

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
