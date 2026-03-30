-- ============================================
-- EducPro — Schema + Test Data
-- ============================================

SET NAMES 'utf8mb4';
SET CHARACTER SET utf8mb4;

-- Table des classes
CREATE TABLE IF NOT EXISTS Class (
  class_id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100) UNIQUE NOT NULL
) DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des professeurs
CREATE TABLE IF NOT EXISTS Teacher (
  teacher_id INT PRIMARY KEY AUTO_INCREMENT,
  first_name VARCHAR(100) NOT NULL,
  last_name VARCHAR(100) NOT NULL,
  mail_teacher VARCHAR(255) UNIQUE,
  password VARCHAR(255),
  is_admin BOOLEAN DEFAULT FALSE,
  topic_name VARCHAR(100)
) DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des étudiants
CREATE TABLE IF NOT EXISTS Student (
  student_id INT PRIMARY KEY AUTO_INCREMENT,
  first_name VARCHAR(100) NOT NULL,
  last_name VARCHAR(100) NOT NULL,
  mail_student VARCHAR(255) UNIQUE,
  password VARCHAR(255),
  class_name VARCHAR(100),
  dob DATE,
  FOREIGN KEY (class_name) REFERENCES Class(name)
    ON DELETE SET NULL 
    ON UPDATE CASCADE
) DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des matières
CREATE TABLE IF NOT EXISTS Topic (
  topic_id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100) UNIQUE NOT NULL,
  teacher_id INT,
  class_id INT
) DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des salles
CREATE TABLE IF NOT EXISTS Room (
  room_id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(50) UNIQUE NOT NULL
) DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des notes
CREATE TABLE IF NOT EXISTS Grade (
  grade_id INT PRIMARY KEY AUTO_INCREMENT,
  grade FLOAT NOT NULL,
  student_id INT NOT NULL,
  topic_name VARCHAR(100) NOT NULL
) DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des emplois du temps (EDT)
CREATE TABLE IF NOT EXISTS EDT (
  slot_id INT PRIMARY KEY AUTO_INCREMENT,
  class_name VARCHAR(100),
  teacher_id INT,
  day_of_week VARCHAR(20) NOT NULL,
  start_time TIME NOT NULL,
  end_time TIME NOT NULL,
  FOREIGN KEY (class_name) REFERENCES Class(name) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (teacher_id) REFERENCES Teacher(teacher_id) ON DELETE CASCADE
) DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des présences (Absences / Retards)
CREATE TABLE IF NOT EXISTS ATTENDANCE (
  attendance_id INT PRIMARY KEY AUTO_INCREMENT,
  student_id INT NOT NULL,
  slot_id INT,
  date_attendance DATE NOT NULL,
  status ENUM('present', 'absent', 'late') DEFAULT 'present',
  justified BOOLEAN DEFAULT FALSE,
  FOREIGN KEY (student_id) REFERENCES Student(student_id) ON DELETE CASCADE,
  FOREIGN KEY (slot_id) REFERENCES EDT(slot_id) ON DELETE SET NULL
) DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table tickets
CREATE TABLE IF NOT EXISTS TICKET (
  ticket_id INT PRIMARY KEY AUTO_INCREMENT,
  msg_content VARCHAR(255),
  teacher_id INT,
  student_id INT
) DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- DONNÉES DE TEST
-- ============================================

-- Classes
INSERT INTO Class (name) VALUES
  ('1ère S-A'), ('1ère S-B'), ('Terminale S'), ('2nde A'), ('BTS SIO');

-- Professeurs (password hashé via bcrypt cost 14)
INSERT INTO Teacher (first_name, last_name, mail_teacher, password, is_admin, topic_name) VALUES
  ('Marie', 'Dupont', 'dupont@educpro.com', '$2b$14$mra1iK7vuHQJZTvVFf.zve6qZLhc86CUvq1QFrhKyVbdmQh0DcHvq', 0, 'Mathématiques'),
  ('Pierre', 'Lefèvre', 'lefevre@educpro.com', '$2b$14$mra1iK7vuHQJZTvVFf.zve6qZLhc86CUvq1QFrhKyVbdmQh0DcHvq', 0, 'Français'),
  ('Sophie', 'Martin', 'martin@educpro.com', '$2b$14$mra1iK7vuHQJZTvVFf.zve6qZLhc86CUvq1QFrhKyVbdmQh0DcHvq', 0, 'Physique-Chimie'),
  ('Jean', 'Bernard', 'bernard@educpro.com', '$2b$14$mra1iK7vuHQJZTvVFf.zve6qZLhc86CUvq1QFrhKyVbdmQh0DcHvq', 0, 'Anglais'),
  ('Claire', 'Admin', 'admin@educpro.com', '$2b$14$BdNIHMf1NPgzR.U/2oxx3.BxWUdS45AJZCceege8ShLlXDK2/DoyK', 1, NULL);

-- Étudiants (password hashé via bcrypt cost 14)
INSERT INTO Student (first_name, last_name, mail_student, password, class_name, dob) VALUES
  ('Lucas', 'Moreau', 'lucas.moreau@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère S-A', '2008-03-15'),
  ('Emma', 'Petit', 'emma.petit@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère S-A', '2008-07-22'),
  ('Hugo', 'Durand', 'hugo.durand@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère S-A', '2008-11-05'),
  ('Léa', 'Leroy', 'lea.leroy@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère S-B', '2008-01-18'),
  ('Nathan', 'Roux', 'nathan.roux@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère S-B', '2008-09-30'),
  ('Chloé', 'David', 'chloe.david@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'Terminale S', '2007-04-12'),
  ('Théo', 'Bertrand', 'theo.bertrand@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'Terminale S', '2007-06-08'),
  ('Manon', 'Lambert', 'manon.lambert@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '2nde A', '2009-02-25'),
  ('Raphaël', 'Garcia', 'raphael.garcia@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '2nde A', '2009-08-14'),
  ('Camille', 'Thomas', 'camille.thomas@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'BTS SIO', '2006-12-03');

-- Matières
INSERT INTO Topic (name, teacher_id, class_id) VALUES
  ('Mathématiques', 1, 1),
  ('Français', 2, 1),
  ('Physique-Chimie', 3, 1),
  ('Anglais', 4, 1),
  ('Mathématiques', 1, 2),
  ('Français', 2, 3);

-- Salles
INSERT INTO Room (name) VALUES
  ('Salle 101'), ('Salle 102'), ('Salle 201'), ('Salle 202'), ('Amphithéâtre A'), ('Labo Physique');

-- Notes
INSERT INTO Grade (grade, student_id, topic_name) VALUES
  (15.5, 1, 'Mathématiques'), (12.0, 1, 'Français'), (14.0, 1, 'Physique-Chimie'), (16.0, 1, 'Anglais'),
  (13.0, 2, 'Mathématiques'), (17.5, 2, 'Français'), (11.0, 2, 'Physique-Chimie'), (14.5, 2, 'Anglais'),
  (18.0, 3, 'Mathématiques'), (10.0, 3, 'Français'), (15.5, 3, 'Physique-Chimie'),
  (9.5, 4, 'Mathématiques'), (14.0, 4, 'Français'),
  (16.0, 5, 'Mathématiques'), (13.5, 5, 'Français'),
  (12.5, 6, 'Mathématiques'), (15.0, 6, 'Français'),
  (11.0, 7, 'Mathématiques'), (16.5, 7, 'Français'),
  (14.0, 8, 'Mathématiques'), (12.0, 8, 'Français'),
  (17.0, 9, 'Mathématiques'),
  (13.5, 10, 'Mathématiques');

-- EDT (emploi du temps — semaine type, lundi = 2026-03-30)
INSERT INTO EDT (topic_name, room_name, teacher_l_name, teacher_f_name, class_name, start_time, end_time) VALUES
  ('Mathématiques', 'Salle 101', 'Dupont', 'Marie', '1ère S-A', '2026-03-30 08:00:00', '2026-03-30 09:30:00'),
  ('Français', 'Salle 102', 'Lefèvre', 'Pierre', '1ère S-A', '2026-03-30 09:45:00', '2026-03-30 11:15:00'),
  ('Physique-Chimie', 'Labo Physique', 'Martin', 'Sophie', '1ère S-A', '2026-03-30 11:30:00', '2026-03-30 13:00:00'),
  ('Anglais', 'Salle 201', 'Bernard', 'Jean', '1ère S-A', '2026-03-30 14:00:00', '2026-03-30 15:30:00'),
  ('Mathématiques', 'Salle 101', 'Dupont', 'Marie', '1ère S-B', '2026-03-30 14:00:00', '2026-03-30 15:30:00'),
  ('Français', 'Salle 102', 'Lefèvre', 'Pierre', '1ère S-B', '2026-03-31 08:00:00', '2026-03-31 09:30:00'),
  ('Mathématiques', 'Salle 201', 'Dupont', 'Marie', 'Terminale S', '2026-03-31 09:45:00', '2026-03-31 11:15:00'),
  ('Français', 'Amphithéâtre A', 'Lefèvre', 'Pierre', 'Terminale S', '2026-04-01 08:00:00', '2026-04-01 09:30:00'),
  ('Mathématiques', 'Salle 101', 'Dupont', 'Marie', '2nde A', '2026-04-01 09:45:00', '2026-04-01 11:15:00'),
  ('Physique-Chimie', 'Labo Physique', 'Martin', 'Sophie', '1ère S-A', '2026-04-01 14:00:00', '2026-04-01 15:30:00'),
  ('Anglais', 'Salle 202', 'Bernard', 'Jean', '1ère S-A', '2026-04-02 08:00:00', '2026-04-02 09:30:00'),
  ('Mathématiques', 'Salle 101', 'Dupont', 'Marie', '1ère S-A', '2026-04-02 09:45:00', '2026-04-02 11:15:00');

-- Absences / Retards
INSERT INTO Attendance (late, absent, student_id) VALUES
  (2, 1, 1), (0, 0, 2), (1, 2, 3), (3, 0, 4), (0, 1, 5),
  (1, 1, 6), (0, 0, 7), (2, 0, 8), (0, 3, 9), (1, 0, 10);