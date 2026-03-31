import pymysql
import bcrypt
import random
import string
import os
from faker import Faker
from dotenv import load_dotenv

load_dotenv()

fake = Faker('fr_FR')

def get_db_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "root"),
        database=os.getenv("DB_NAME", "educpro"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )

def hash_password(password, cost=10):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(cost)).decode('utf-8')

def generate_complex_password(length=12):
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choice(characters) for i in range(length))

def main():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Update existing users passwords
    print("Updating existing users...")
    
    cursor.execute("SELECT student_id, mail_student FROM Student")
    students = cursor.fetchall()
    for s in students:
        new_pwd = generate_complex_password()
        hashed = hash_password(new_pwd, 14)
        cursor.execute("UPDATE Student SET password=%s WHERE student_id=%s", (hashed, s['student_id']))

    cursor.execute("SELECT teacher_id, mail_teacher FROM Teacher")
    teachers = cursor.fetchall()
    for t in teachers:
        new_pwd = generate_complex_password()
        hashed = hash_password(new_pwd, 14)
        cursor.execute("UPDATE Teacher SET password=%s WHERE teacher_id=%s", (hashed, t['teacher_id']))

    print(f"Updated {len(students)} students and {len(teachers)} teachers passwords.")

    # Generate test accounts
    test_student_pwd = generate_complex_password()
    test_teacher_pwd = generate_complex_password()
    test_admin_pwd = generate_complex_password()

    test_student = {
        'first': fake.first_name(),
        'last': fake.last_name(),
        'email': 'test_student@educpro.fr',
        'pwd': test_student_pwd,
        'class': 'Terminale S'
    }

    test_teacher = {
        'first': fake.first_name(),
        'last': fake.last_name(),
        'email': 'test_teacher@educpro.fr',
        'pwd': test_teacher_pwd,
        'topic': 'Mathématiques',
        'is_admin': 0
    }

    test_admin = {
        'first': fake.first_name(),
        'last': fake.last_name(),
        'email': 'test_admin@educpro.fr',
        'pwd': test_admin_pwd,
        'topic': 'Informatique',
        'is_admin': 1
    }

    print("--- TEST ACCOUNTS ---")
    print(f"Student: {test_student['email']} / {test_student['pwd']}")
    print(f"Teacher: {test_teacher['email']} / {test_teacher['pwd']}")
    print(f"Admin: {test_admin['email']} / {test_admin['pwd']}")

    # Insert test accounts
    cursor.execute("INSERT INTO Student (first_name, last_name, mail_student, password, class_name) VALUES (%s, %s, %s, %s, %s)",
                   (test_student['first'], test_student['last'], test_student['email'], hash_password(test_student['pwd'], 14), test_student['class']))
                   
    cursor.execute("INSERT INTO Teacher (first_name, last_name, mail_teacher, password, topic_name, is_admin) VALUES (%s, %s, %s, %s, %s, %s)",
                   (test_teacher['first'], test_teacher['last'], test_teacher['email'], hash_password(test_teacher['pwd'], 14), test_teacher['topic'], test_teacher['is_admin']))

    cursor.execute("INSERT INTO Teacher (first_name, last_name, mail_teacher, password, topic_name, is_admin) VALUES (%s, %s, %s, %s, %s, %s)",
                   (test_admin['first'], test_admin['last'], test_admin['email'], hash_password(test_admin['pwd'], 14), test_admin['topic'], test_admin['is_admin']))

    print("Fetching existing classes and topics...")
    cursor.execute("SELECT name FROM Class")
    classes = [row['name'] for row in cursor.fetchall()]
    if not classes:
        print("No classes found in DB! Creating some...")
        classes = ['Seconde A', 'Seconde B', 'Premiere L', 'Premiere S', 'Terminale L', 'Terminale S', 'BTS 1', 'BTS 2']
        for c in classes:
            cursor.execute("INSERT IGNORE INTO Class (name) VALUES (%s)", (c,))
    
    # We will just insert the string topic_name into Teacher as before.
    # If there's a Topic table referencing teacher, we should check it.
    
    print("Inserting 949 students...")
    # Insert 949 additional students
    for i in range(949):
        first = fake.first_name()
        last = fake.last_name()
        email = f"{first.lower()}_{last.lower()}_{i}@student.educpro.fr"
        pwd = generate_complex_password()
        hashed = hash_password(pwd, 10)
        cname = random.choice(classes)
        cursor.execute("INSERT INTO Student (first_name, last_name, mail_student, password, class_name) VALUES (%s, %s, %s, %s, %s)",
                       (first, last, email, hashed, cname))

    print("Inserting 47 teachers...")
    topics = ['Mathématiques', 'Physique', 'Chimie', 'Histoire', 'Géographie', 'Français', 'Anglais', 'Espagnol', 'Philo']
    # Insert 47 additional teachers
    for i in range(47):
        first = fake.first_name()
        last = fake.last_name()
        email = f"{first.lower()}_{last.lower()}_{i}@educpro.fr".replace(" ", "_")
        pwd = generate_complex_password()
        hashed = hash_password(pwd, 10)
        topic = random.choice(topics)
        cursor.execute("INSERT INTO Teacher (first_name, last_name, mail_teacher, password, topic_name, is_admin) VALUES (%s, %s, %s, %s, %s, %s)",
                       (first, last, email, hashed, topic, 0))
        # if the system uses Topic table to link teacher to topic, do it here
        # cursor.execute("INSERT INTO Topic (name, teacher_id) VALUES (%s, %s)", (topic, cursor.lastrowid))

    print("Inserting 1 admin...")
    admin_first = fake.first_name()
    admin_last = fake.last_name()
    admin_email = f"admin_{admin_last.lower().replace(' ', '_')}@educpro.fr"
    cursor.execute("INSERT INTO Teacher (first_name, last_name, mail_teacher, password, topic_name, is_admin) VALUES (%s, %s, %s, %s, %s, %s)",
                   (admin_first, admin_last, admin_email, hash_password(generate_complex_password(), 10), 'Direction', 1))

    conn.commit()
    conn.close()
    print("Done!")

if __name__ == '__main__':
    main()
