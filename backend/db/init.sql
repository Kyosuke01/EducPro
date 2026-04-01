-- ============================================
-- EducPro — Schema + Test Data
-- ============================================

SET NAMES 'utf8mb4';
SET CHARACTER SET utf8mb4;

-- Table des professeurs
CREATE TABLE IF NOT EXISTS Teacher (
  teacher_id INT PRIMARY KEY AUTO_INCREMENT,
  first_name VARCHAR(100) NOT NULL,
  last_name VARCHAR(100) NOT NULL,
  mail_teacher VARCHAR(255) UNIQUE,
  password VARCHAR(255),
  is_admin BOOLEAN DEFAULT FALSE,
  topic_name VARCHAR(100),
  totp_secret VARCHAR(32) DEFAULT NULL
) DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des classes
CREATE TABLE IF NOT EXISTS Class (
  class_id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100) UNIQUE NOT NULL,
  max_capacity INT NOT NULL DEFAULT 35,
  homeroom_teacher_id INT NULL,
  FOREIGN KEY (homeroom_teacher_id) REFERENCES Teacher(teacher_id)
    ON DELETE SET NULL
    ON UPDATE CASCADE
) DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des étudiants
CREATE TABLE IF NOT EXISTS Student (
  student_id INT PRIMARY KEY AUTO_INCREMENT,
  first_name VARCHAR(100) NOT NULL,
  last_name VARCHAR(100) NOT NULL,
  mail_student VARCHAR(255) UNIQUE,
  password VARCHAR(255),
  totp_secret VARCHAR(32) DEFAULT NULL,
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

-- Table tickets (conversation)
CREATE TABLE IF NOT EXISTS SupportTicket (
  ticket_id INT PRIMARY KEY AUTO_INCREMENT,
  subject VARCHAR(150) NOT NULL,
  student_id INT NULL,
  teacher_id INT NULL,
  created_by_role ENUM('student','teacher','admin') NOT NULL,
  created_by_id INT NOT NULL,
  status ENUM('open','pending','closed') DEFAULT 'open',
  priority ENUM('normal','high','urgent') DEFAULT 'normal',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS SupportMessage (
  message_id INT PRIMARY KEY AUTO_INCREMENT,
  ticket_id INT NOT NULL,
  sender_role ENUM('student','teacher','admin') NOT NULL,
  sender_id INT NOT NULL,
  body TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (ticket_id) REFERENCES SupportTicket(ticket_id) ON DELETE CASCADE
) DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- DONNÉES DE TEST
-- ============================================

-- Classes
INSERT INTO Class (name, max_capacity) VALUES
  ('1ère S-A', 35),
  ('1ère S-B', 35),
  ('Terminale S', 35),
  ('2nde A', 35),
  ('2nde B', 35),
  ('2nde C', 35),
  ('1ère STMG A', 35),
  ('Terminale STMG', 35),
  ('BTS SIO', 35),
  ('BTS CG', 35);

-- Professeurs (password hashé via bcrypt cost 14)
INSERT INTO Teacher (first_name, last_name, mail_teacher, password, is_admin, topic_name) VALUES
  ('Marie', 'Dupont', 'dupont@educpro.com', '$2b$14$mra1iK7vuHQJZTvVFf.zve6qZLhc86CUvq1QFrhKyVbdmQh0DcHvq', 0, 'Mathématiques'),
  ('Pierre', 'Lefèvre', 'lefevre@educpro.com', '$2b$14$mra1iK7vuHQJZTvVFf.zve6qZLhc86CUvq1QFrhKyVbdmQh0DcHvq', 0, 'Français'),
  ('Sophie', 'Martin', 'martin@educpro.com', '$2b$14$mra1iK7vuHQJZTvVFf.zve6qZLhc86CUvq1QFrhKyVbdmQh0DcHvq', 0, 'Physique-Chimie'),
  ('Jean', 'Bernard', 'bernard@educpro.com', '$2b$14$mra1iK7vuHQJZTvVFf.zve6qZLhc86CUvq1QFrhKyVbdmQh0DcHvq', 0, 'Anglais'),
  ('Claire', 'Admin', 'admin@educpro.com', '$2b$14$BdNIHMf1NPgzR.U/2oxx3.BxWUdS45AJZCceege8ShLlXDK2/DoyK', 1, NULL),
  ('Alex', 'SuperAdmin', 'alex.superadmin@educpro.com', '$2b$12$uL1kdPrul3ZK5WqLXRaEpuqQuY0SSz8nIvEEAW0sszMlx.t7hjbOm', 1, NULL),
  ('Isabelle', 'Morel', 'morel@educpro.com', '$2b$14$mra1iK7vuHQJZTvVFf.zve6qZLhc86CUvq1QFrhKyVbdmQh0DcHvq', 0, 'Économie-Gestion'),
  ('Marc', 'Petit', 'petit@educpro.com', '$2b$14$mra1iK7vuHQJZTvVFf.zve6qZLhc86CUvq1QFrhKyVbdmQh0DcHvq', 0, 'Histoire-Géo'),
  ('Aline', 'Roussel', 'roussel@educpro.com', '$2b$14$mra1iK7vuHQJZTvVFf.zve6qZLhc86CUvq1QFrhKyVbdmQh0DcHvq', 0, 'Management'),
  ('Victor', 'Schmitt', 'schmitt@educpro.com', '$2b$14$mra1iK7vuHQJZTvVFf.zve6qZLhc86CUvq1QFrhKyVbdmQh0DcHvq', 0, 'Informatique'),
  ('Hélène', 'Dubois', 'dubois@educpro.com', '$2b$14$mra1iK7vuHQJZTvVFf.zve6qZLhc86CUvq1QFrhKyVbdmQh0DcHvq', 0, 'Comptabilité');

-- Attribution des professeurs principaux aux classes
UPDATE Class SET homeroom_teacher_id = (SELECT teacher_id FROM Teacher WHERE mail_teacher = 'dupont@educpro.com') WHERE name = '1ère S-A';
UPDATE Class SET homeroom_teacher_id = (SELECT teacher_id FROM Teacher WHERE mail_teacher = 'lefevre@educpro.com') WHERE name = '1ère S-B';
UPDATE Class SET homeroom_teacher_id = (SELECT teacher_id FROM Teacher WHERE mail_teacher = 'martin@educpro.com') WHERE name = 'Terminale S';
UPDATE Class SET homeroom_teacher_id = (SELECT teacher_id FROM Teacher WHERE mail_teacher = 'bernard@educpro.com') WHERE name = '2nde A';
UPDATE Class SET homeroom_teacher_id = (SELECT teacher_id FROM Teacher WHERE mail_teacher = 'admin@educpro.com') WHERE name = 'BTS SIO';
UPDATE Class SET homeroom_teacher_id = (SELECT teacher_id FROM Teacher WHERE mail_teacher = 'morel@educpro.com') WHERE name = '1ère STMG A';
UPDATE Class SET homeroom_teacher_id = (SELECT teacher_id FROM Teacher WHERE mail_teacher = 'petit@educpro.com') WHERE name = 'Terminale STMG';
UPDATE Class SET homeroom_teacher_id = (SELECT teacher_id FROM Teacher WHERE mail_teacher = 'roussel@educpro.com') WHERE name = '2nde B';
UPDATE Class SET homeroom_teacher_id = (SELECT teacher_id FROM Teacher WHERE mail_teacher = 'schmitt@educpro.com') WHERE name = '2nde C';
UPDATE Class SET homeroom_teacher_id = (SELECT teacher_id FROM Teacher WHERE mail_teacher = 'dubois@educpro.com') WHERE name = 'BTS CG';

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
  ('Camille', 'Thomas', 'camille.thomas@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'BTS SIO', '2006-12-03'),
  ('Noah', 'Carpentier', 'noah.carpentier@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère STMG A', '2008-05-10'),
  ('Inès', 'Marchand', 'ines.marchand@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère STMG A', '2008-02-17'),
  ('Ethan', 'Millet', 'ethan.millet@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère STMG A', '2008-10-03'),
  ('Sara', 'Boutin', 'sara.boutin@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'Terminale STMG', '2007-01-29'),
  ('Adam', 'Gaillard', 'adam.gaillard@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'Terminale STMG', '2007-07-12'),
  ('Lina', 'Rodier', 'lina.rodier@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'Terminale STMG', '2007-03-07'),
  ('Gabriel', 'Chartier', 'gabriel.chartier@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '2nde B', '2009-05-21'),
  ('Zoé', 'Bailly', 'zoe.bailly@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '2nde B', '2009-09-11'),
  ('Clément', 'Pires', 'clement.pires@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '2nde B', '2009-12-02'),
  ('Maya', 'Humbert', 'maya.humbert@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '2nde C', '2009-01-15'),
  ('Louis', 'Benali', 'louis.benali@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '2nde C', '2009-06-19'),
  ('Aya', 'Dufour', 'aya.dufour@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '2nde C', '2009-10-24'),
  ('Yanis', 'Leger', 'yanis.leger@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'BTS SIO', '2006-03-09'),
  ('Océane', 'Verdier', 'oceane.verdier@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'BTS SIO', '2006-05-18'),
  ('Tom', 'Laporte', 'tom.laporte@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'BTS CG', '2006-09-27'),
  ('Jade', 'Paquet', 'jade.paquet@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'BTS CG', '2006-11-14'),
  ('Maël', 'Riou', 'mael.riou@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'BTS CG', '2006-01-05'),
  ('Salomé', 'Renaud', 'salome.renaud@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'Terminale S', '2007-08-30'),
  ('Enzo', 'Delcourt', 'enzo.delcourt@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère S-B', '2008-05-02');

-- Matières
INSERT INTO Topic (name, teacher_id, class_id) VALUES
  ('Mathématiques', 1, 1),
  ('Français', 2, 1),
  ('Physique-Chimie', 3, 1),
  ('Anglais', 4, 1),
  ('Histoire-Géo', 8, 1),
  ('Arts Plastiques', 5, 2);

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

-- EDT (emploi du temps — semaine type)
INSERT INTO EDT (class_name, teacher_id, day_of_week, start_time, end_time) VALUES
  ('1ère S-A', 1, 'lundi', '08:00:00', '09:30:00'),
  ('1ère S-A', 2, 'lundi', '09:45:00', '11:15:00'),
  ('1ère S-A', 3, 'lundi', '11:30:00', '13:00:00'),
  ('1ère S-A', 4, 'lundi', '14:00:00', '15:30:00'),
  ('1ère S-B', 1, 'mardi', '14:00:00', '15:30:00'),
  ('1ère S-B', 2, 'mardi', '08:00:00', '09:30:00'),
  ('Terminale S', 1, 'mardi', '09:45:00', '11:15:00'),
  ('Terminale S', 2, 'mercredi', '08:00:00', '09:30:00'),
  ('2nde A', 1, 'mercredi', '09:45:00', '11:15:00'),
  ('1ère S-A', 3, 'jeudi', '14:00:00', '15:30:00'),
  ('1ère S-A', 4, 'jeudi', '08:00:00', '09:30:00'),
  ('1ère S-A', 1, 'vendredi', '09:45:00', '11:15:00');

-- Absences / Retards (Correction des colonnes)
INSERT INTO ATTENDANCE (student_id, slot_id, date_attendance, status, justified) VALUES
  (1, 1, '2026-03-30', 'absent', FALSE),
  (2, 1, '2026-03-30', 'late', TRUE),
  (3, 2, '2026-03-30', 'absent', FALSE);

-- ============================================
-- MEGA SEED (200 Étudiants + Nouvelles Classes / Professeurs)
-- ============================================

INSERT INTO Class (name, max_capacity) VALUES
  ('3ème A', 35),
  ('3ème B', 35),
  ('1ère L', 35),
  ('Terminale L', 35);

INSERT INTO Teacher (first_name, last_name, mail_teacher, password, is_admin, topic_name) VALUES
  ('Gilles', 'Moulin', 'moulin@educpro.com', '$2b$14$mra1iK7vuHQJZTvVFf.zve6qZLhc86CUvq1QFrhKyVbdmQh0DcHvq', 0, 'Arts Plastiques'),
  ('Camille', 'Blanc', 'blanc@educpro.com', '$2b$14$mra1iK7vuHQJZTvVFf.zve6qZLhc86CUvq1QFrhKyVbdmQh0DcHvq', 0, 'Musique'),
  ('Paul', 'Garnier', 'garnier@educpro.com', '$2b$14$mra1iK7vuHQJZTvVFf.zve6qZLhc86CUvq1QFrhKyVbdmQh0DcHvq', 0, 'Philosophie'),
  ('Céline', 'Faure', 'faure@educpro.com', '$2b$14$mra1iK7vuHQJZTvVFf.zve6qZLhc86CUvq1QFrhKyVbdmQh0DcHvq', 0, 'Lettres');

UPDATE Class SET homeroom_teacher_id = (SELECT teacher_id FROM Teacher WHERE mail_teacher = 'moulin@educpro.com') WHERE name = '3ème A';
UPDATE Class SET homeroom_teacher_id = (SELECT teacher_id FROM Teacher WHERE mail_teacher = 'blanc@educpro.com') WHERE name = '3ème B';
UPDATE Class SET homeroom_teacher_id = (SELECT teacher_id FROM Teacher WHERE mail_teacher = 'garnier@educpro.com') WHERE name = '1ère L';
UPDATE Class SET homeroom_teacher_id = (SELECT teacher_id FROM Teacher WHERE mail_teacher = 'faure@educpro.com') WHERE name = 'Terminale L';

INSERT INTO Student (first_name, last_name, mail_student, password, class_name, dob) VALUES
  ('Arthur', 'Martin', 'arthur.martin@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '3ème A', '2010-04-12'),
  ('Louise', 'Bernard', 'louise.bernard@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '3ème A', '2010-06-25'),
  ('Maël', 'Dubois', 'mael.dubois@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '3ème A', '2010-01-08'),
  ('Jade', 'Thomas', 'jade.thomas@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '3ème A', '2010-09-17'),
  ('Jules', 'Robert', 'jules.robert@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '3ème A', '2010-05-05'),
  ('Ambre', 'Richard', 'ambre.richard@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '3ème A', '2010-12-21'),
  ('Léo', 'Petit', 'leo.petit@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '3ème A', '2010-03-14'),
  ('Alice', 'Durand', 'alice.durand@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '3ème A', '2010-11-09'),
  ('Gabin', 'Leroy', 'gabin.leroy@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '3ème A', '2010-02-28'),
  ('Rose', 'Moreau', 'rose.moreau@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '3ème B', '2010-07-07'),
  ('Hugo', 'Simon', 'hugo.simon@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '3ème B', '2010-08-30'),
  ('Mila', 'Laurent', 'mila.laurent@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '3ème B', '2010-10-15'),
  ('Tiago', 'Lefèvre', 'tiago.lefevre@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '3ème B', '2010-04-04'),
  ('Mia', 'Michel', 'mila.michel@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '3ème B', '2010-12-10'),
  ('Eden', 'Garcia', 'eden.garcia@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '3ème B', '2010-05-22'),
  ('Elena', 'David', 'elena.david@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '3ème B', '2010-01-31'),
  ('Sacha', 'Bertrand', 'sacha.bertrand@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '3ème B', '2010-09-08'),
  ('Julia', 'Roux', 'julia.roux@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '3ème B', '2010-03-03'),
  ('Aaron', 'Vincent', 'adam.vincent@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '3ème B', '2010-11-27'),
  ('Inès', 'Fournier', 'ines.fournier@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère L', '2008-04-18'),
  ('Léon', 'Morel', 'leo.morel@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère L', '2008-08-09'),
  ('Zoé', 'Girard', 'zoe.girard@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère L', '2008-02-12'),
  ('Paul', 'Andre', 'paul.andre@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère L', '2008-10-05'),
  ('Lola', 'Lefevre', 'lola.lefevre@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère L', '2008-06-22'),
  ('Noé', 'Mercier', 'noah.mercier@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère L', '2008-12-14'),
  ('Agathe', 'Dupont', 'agathe.dupont@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère L', '2008-07-02'),
  ('Malo', 'Garnier', 'malo.garnier@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère L', '2008-03-28'),
  ('Lina', 'Lambert', 'lina.lambert@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère L', '2008-09-11'),
  ('Marceau', 'Blanc', 'marceau.blanc@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'Terminale L', '2007-05-16'),
  ('Margaux', 'Guerin', 'margaux.guerin@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'Terminale L', '2007-01-29'),
  ('Côme', 'Colin', 'come.colin@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'Terminale L', '2007-11-20'),
  ('Romane', 'Pellegrini', 'romane.pellegrini@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'Terminale L', '2007-08-06'),
  ('Marius', 'Marchand', 'marius.marchand@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'Terminale L', '2007-12-05'),
  ('Lucie', 'Boyer', 'lucie.boyer@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'Terminale L', '2007-02-18'),
  ('Naël', 'Gauthier', 'nathan.gauthier@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'Terminale L', '2007-07-24'),
  ('Alix', 'Perrin', 'alice.perrin@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'Terminale L', '2007-10-10'),
  ('Nino', 'Chevalier', 'noah.chevalier@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'Terminale L', '2007-04-14'),
  ('Clara', 'Lemaire', 'c.lem0@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère S-A', '2008-02-01'),
  ('Evan', 'Mathieu', 'e.math1@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère S-B', '2008-03-02'),
  ('Nina', 'Clement', 'n.clem2@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'Terminale S', '2007-04-03'),
  ('Robin', 'Gillet', 'r.gil3@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '2nde A', '2009-05-04'),
  ('Sarah', 'Vidal', 's.vid4@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '2nde B', '2009-06-05'),
  ('Tom', 'Roussel', 't.rou5@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '2nde C', '2009-07-06'),
  ('Iris', 'Gaudin', 'i.gau6@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère STMG A', '2008-08-07'),
  ('Timéo', 'Dumont', 't.dum7@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'Terminale STMG', '2007-09-08'),
  ('Anaïs', 'Guillot', 'a.gui8@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'BTS SIO', '2006-10-09'),
  ('Axel', 'Colin', 'a.col9@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'BTS CG', '2006-11-10'),
  ('Clémence', 'Le gall', 'c.leg10@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '3ème A', '2010-12-11'),
  ('Antoine', 'Denis', 'a.den11@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '3ème B', '2010-01-12'),
  ('Apolline', 'Hubert', 'a.hub12@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère L', '2008-02-13'),
  ('Mathis', 'Pichon', 'm.pic13@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'Terminale L', '2007-03-14'),
  ('Léonie', 'Riviere', 'l.riv14@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère S-A', '2008-04-15'),
  ('Gaspard', 'Meunier', 'g.meu15@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère S-B', '2008-05-16'),
  ('Jeanne', 'Renard', 'j.ren16@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'Terminale S', '2007-06-17'),
  ('Baptiste', 'Carpentier', 'b.car17@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '2nde A', '2009-07-18'),
  ('Valentine', 'Bailly', 'v.bai18@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '2nde B', '2009-08-19'),
  ('Noé', 'Brun', 'n.bru19@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '2nde C', '2009-09-20'),
  ('Capucine', 'Gautier', 'c.gau20@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère STMG A', '2008-10-21'),
  ('Marin', 'Rey', 'm.rey21@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'Terminale STMG', '2007-11-22'),
  ('Justine', 'Huet', 'j.hue22@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'BTS SIO', '2006-12-23'),
  ('Basile', 'Barbier', 'b.bar23@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'BTS CG', '2006-01-24'),
  ('Eline', 'Blanchard', 'e.bla24@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '3ème A', '2010-02-25'),
  ('Martin', 'Caron', 'm.car25@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '3ème B', '2010-03-26'),
  ('Zélie', 'Lebrun', 'z.leb26@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère L', '2008-04-27'),
  ('Malo', 'Schmitt', 'm.sch27@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'Terminale L', '2007-05-28'),
  ('Diane', 'Giraud', 'd.gir28@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère S-A', '2008-06-29'),
  ('Simon', 'Charles', 's.cha29@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère S-B', '2008-07-30'),
  ('Célia', 'Rousseau', 'c.rou30@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'Terminale S', '2007-08-31'),
  ('Maxime', 'Jacquet', 'm.jac31@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '2nde A', '2009-09-01'),
  ('Lilou', 'Martel', 'l.mar32@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '2nde B', '2009-10-02'),
  ('Tristan', 'Vasseur', 't.vas33@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '2nde C', '2009-11-03'),
  ('Tess', 'Picard', 't.pic34@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère STMG A', '2008-12-04'),
  ('Oscar', 'Dumas', 'o.dum35@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'Terminale STMG', '2007-01-05'),
  ('Margot', 'Boucher', 'm.bou36@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'BTS SIO', '2006-02-06'),
  ('Maceo', 'Bourgeois', 'm.bou37@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'BTS CG', '2006-03-07'),
  ('Mathilde', 'Olivier', 'm.oli38@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '3ème A', '2010-04-08'),
  ('Colin', 'Poirier', 'c.poi39@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '3ème B', '2010-05-09'),
  ('Romy', 'Noel', 'r.noe40@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère L', '2008-06-10'),
  ('Ewan', 'Lemaigre', 'e.lem41@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'Terminale L', '2007-07-11'),
  ('Albane', 'Benoit', 'a.ben42@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère S-A', '2008-08-12'),
  ('Eliott', 'Aubert', 'e.aub43@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère S-B', '2008-09-13'),
  ('Héloïse', 'Villard', 'h.vil44@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'Terminale S', '2007-10-14'),
  ('Titouan', 'Nicolas', 't.nic45@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '2nde A', '2009-11-15'),
  ('Eloïse', 'Lecomte', 'e.lec46@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '2nde B', '2009-12-16'),
  ('Lilian', 'Meyer', 'l.meu47@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '2nde C', '2009-01-17'),
  ('Lison', 'Blanc', 'l.bla48@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère STMG A', '2008-02-18'),
  ('Auguste', 'Rougier', 'a.rou49@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'Terminale STMG', '2007-03-19'),
  ('Lou', 'Guillaume', 'l.gui50@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'BTS SIO', '2006-04-20'),
  ('Valentin', 'Mathis', 'v.mat51@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'BTS CG', '2006-05-21'),
  ('Flavie', 'Rolland', 'f.rol52@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '3ème A', '2010-06-22'),
  ('Soan', 'Masse', 's.mas53@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '3ème B', '2010-07-23'),
  ('Cassandre', 'Collin', 'c.col54@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère L', '2008-08-24'),
  ('Maé', 'Garcia', 'm.gar55@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'Terminale L', '2007-09-25'),
  ('Coline', 'Leveque', 'c.lev56@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère S-A', '2008-10-26'),
  ('Joan', 'Pruvost', 'j.pru57@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère S-B', '2008-11-27'),
  ('Thaïs', 'Morin', 't.mor58@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'Terminale S', '2007-12-28'),
  ('Noam', 'Muller', 'n.mul59@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '2nde A', '2009-01-29'),
  ('Roxane', 'Colin', 'r.col60@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '2nde B', '2009-02-01'),
  ('Lenny', 'Perrot', 'l.per61@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '2nde C', '2009-03-02'),
  ('Constance', 'Faure', 'c.fau62@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère STMG A', '2008-04-03'),
  ('Naël', 'Guyot', 'n.gui63@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'Terminale STMG', '2007-05-04'),
  ('Fanny', 'Bouvier', 'f.bou64@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'BTS SIO', '2006-06-05'),
  ('Ulysse', 'Toulouse', 'u.tou65@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'BTS CG', '2006-07-06'),
  ('Adèle', 'Besson', 'a.bes66@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '3ème A', '2010-08-07'),
  ('Corentin', 'Pasquier', 'c.pas67@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '3ème B', '2010-09-08'),
  ('Suzanne', 'Masson', 's.mas68@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère L', '2008-10-09'),
  ('Armand', 'Maillard', 'a.mai69@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'Terminale L', '2007-11-10'),
  ('Lily', 'Gillet', 'l.gil70@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère S-A', '2008-12-11'),
  ('Ismaël', 'Roche', 'i.roc71@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère S-B', '2008-01-12'),
  ('Clarisse', 'Lemoine', 'c.lem72@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'Terminale S', '2007-02-13'),
  ('Ruben', 'Menard', 'r.men73@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '2nde A', '2009-03-14'),
  ('Olivia', 'Renault', 'o.ren74@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '2nde B', '2009-04-15'),
  ('Yanis', 'Fleury', 'y.fle75@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '2nde C', '2009-05-16'),
  ('Noémie', 'Evrard', 'n.eve76@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère STMG A', '2008-06-17'),
  ('Milan', 'Goulet', 'm.gou77@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'Terminale STMG', '2007-07-18'),
  ('Maëlys', 'Rocher', 'm.roc78@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'BTS SIO', '2006-08-19'),
  ('Anton', 'Barre', 'a.bar79@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'BTS CG', '2006-09-20'),
  ('Lya', 'Ferreira', 'l.fer80@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '3ème A', '2010-10-21'),
  ('Soren', 'Valentin', 's.val81@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '3ème B', '2010-11-22'),
  ('Léana', 'Lopes', 'l.lop82@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère L', '2008-12-23'),
  ('Victor', 'Monnier', 'v.mon83@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'Terminale L', '2007-01-24'),
  ('Anaëlle', 'Jacques', 'a.jac84@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère S-A', '2008-02-25'),
  ('Gauthier', 'Deschamps', 'g.des85@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère S-B', '2008-03-26'),
  ('Elise', 'Marty', 'e.mar86@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'Terminale S', '2007-04-27'),
  ('Samuel', 'Benoist', 's.ben87@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '2nde A', '2009-05-28'),
  ('Charlie', 'Guilbert', 'c.gui88@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '2nde B', '2009-06-29'),
  ('Pablo', 'Mallet', 'p.mal89@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '2nde C', '2009-07-30'),
  ('Zia', 'Lacroix', 'z.lac90@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère STMG A', '2008-08-31'),
  ('Noham', 'Legrand', 'n.leg91@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'Terminale STMG', '2007-09-01'),
  ('Victoire', 'Perrier', 'v.per92@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'BTS SIO', '2006-10-02'),
  ('Elian', 'Grondin', 'e.gro93@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'BTS CG', '2006-11-03'),
  ('Albane', 'Navarro', 'a.nav94@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '3ème A', '2010-12-04'),
  ('Naël', 'Tessier', 'n.tes95@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '3ème B', '2010-01-05'),
  ('Hélèna', 'Bourdon', 'h.bou96@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère L', '2008-02-06'),
  ('Colin', 'Larcher', 'c.lar97@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'Terminale L', '2007-03-07'),
  ('Faustine', 'Remy', 'f.rem98@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère S-A', '2008-04-08'),
  ('Diego', 'Rossi', 'd.ros99@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère S-B', '2008-05-09'),
  ('Soline', 'Camus', 's.cam100@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'Terminale S', '2007-06-10'),
  ('Alexis', 'Courtois', 'a.cou101@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '2nde A', '2009-07-11'),
  ('Solène', 'Poulain', 's.pou102@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '2nde B', '2009-08-12'),
  ('Camil', 'Dumas', 'c.dum103@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '2nde C', '2009-09-13'),
  ('Bérénice', 'Michaud', 'b.mic104@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère STMG A', '2008-10-14'),
  ('Dorian', 'Baudry', 'd.bau105@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'Terminale STMG', '2007-11-15'),
  ('Mélina', 'Joubert', 'm.jou106@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'BTS SIO', '2006-12-16'),
  ('Nathanaël', 'Chauvin', 'n.cha107@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'BTS CG', '2006-01-17'),
  ('Zélie', 'Vasseur', 'z.vas108@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '3ème A', '2010-02-18'),
  ('Estéban', 'Maurice', 'e.mau109@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '3ème B', '2010-03-19'),
  ('Amandine', 'Allard', 'a.all110@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère L', '2008-04-20'),
  ('Aubin', 'Lombard', 'a.lom111@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'Terminale L', '2007-05-21'),
  ('Lylou', 'Raynaud', 'l.ray112@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère S-A', '2008-06-22'),
  ('Corentin', 'Letellier', 'c.let113@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère S-B', '2008-07-23'),
  ('Célestine', 'Couturier', 'c.cou114@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'Terminale S', '2007-08-24'),
  ('Joachim', 'Millet', 'j.mil115@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '2nde A', '2009-09-25'),
  ('Mathilde', 'Boulay', 'm.bou116@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '2nde B', '2009-10-26'),
  ('Joris', 'Breton', 'j.bre117@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '2nde C', '2009-11-27'),
  ('Garance', 'Boutin', 'g.bou118@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère STMG A', '2008-12-28'),
  ('Maxence', 'Albert', 'm.alb119@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'Terminale STMG', '2007-01-29'),
  ('Perrine', 'Bodin', 'p.bod120@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'BTS SIO', '2006-02-01'),
  ('Camil', 'Collet', 'c.col121@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'BTS CG', '2006-03-02'),
  ('Maïwenn', 'Peyre', 'm.pey122@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '3ème A', '2010-04-03'),
  ('Ayoub', 'Leduc', 'a.led123@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '3ème B', '2010-05-04'),
  ('Lana', 'Guichard', 'l.gui124@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère L', '2008-06-05'),
  ('Noa', 'Besson', 'n.bes125@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'Terminale L', '2007-07-06'),
  ('Nélya', 'Le gall', 'n.leg126@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère S-A', '2008-08-07'),
  ('Côme', 'Muller', 'c.mul127@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère S-B', '2008-09-08'),
  ('Lise', 'Benoit', 'l.ben128@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'Terminale S', '2007-10-09'),
  ('Ilyès', 'Garcia', 'i.gar129@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '2nde A', '2009-11-10'),
  ('Cléa', 'Boucher', 'c.bou130@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '2nde B', '2009-12-11'),
  ('Naël', 'Dumas', 'n.dum131@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '2nde C', '2009-01-12'),
  ('Soline', 'Roussel', 's.rou132@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère STMG A', '2008-02-13'),
  ('Maëlan', 'Vidal', 'm.vid133@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'Terminale STMG', '2007-03-14'),
  ('Mélody', 'Gillet', 'm.gil134@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'BTS SIO', '2006-04-15'),
  ('Ewan', 'Clement', 'e.cle135@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'BTS CG', '2006-05-16'),
  ('Romane', 'Mathieu', 'r.mat136@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '3ème A', '2010-06-17'),
  ('Kylian', 'Lemaire', 'k.lem137@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '3ème B', '2010-07-18'),
  ('Agathe', 'Chevalier', 'a.che138@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère L', '2008-08-19'),
  ('Timothée', 'Perrin', 't.per139@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'Terminale L', '2007-09-20'),
  ('Hanaé', 'Gauthier', 'h.gau140@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère S-A', '2008-10-21'),
  ('Malo', 'Boyer', 'm.boy141@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère S-B', '2008-11-22'),
  ('Lily', 'Marchand', 'l.mar142@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'Terminale S', '2007-12-23'),
  ('Antonin', 'Pellegrini', 'a.pel143@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '2nde A', '2009-01-24'),
  ('Apolline', 'Colin', 'a.col144@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '2nde B', '2009-02-25'),
  ('Soan', 'Guerin', 's.gue145@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '2nde C', '2009-03-26'),
  ('Coline', 'Blanc', 'c.bla146@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère STMG A', '2008-04-27'),
  ('Aloïs', 'Lambert', 'a.lam147@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'Terminale STMG', '2007-05-28'),
  ('Eloïse', 'Garnier', 'e.gar148@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'BTS SIO', '2006-06-29'),
  ('Titouan', 'Dupont', 't.dup149@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'BTS CG', '2006-07-30'),
  ('Candice', 'Mercier', 'c.mer150@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '3ème A', '2010-08-31'),
  ('Julian', 'Lefevre', 'j.lef151@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '3ème B', '2010-09-01'),
  ('Zélie', 'Andre', 'z.and152@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère L', '2008-10-02'),
  ('Estéban', 'Girard', 'e.gir153@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'Terminale L', '2007-11-03'),
  ('Thaïs', 'Morel', 't.mor154@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère S-A', '2008-12-04'),
  ('Noham', 'Fournier', 'n.fou155@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère S-B', '2008-01-05'),
  ('Lana', 'Vincent', 'l.vin156@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', 'Terminale S', '2007-02-06'),
  ('Joan', 'Roux', 'j.rou157@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '2nde A', '2009-03-07'),
  ('Soline', 'Bertrand', 's.ber158@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '2nde B', '2009-04-08'),
  ('Diego', 'David', 'd.dav159@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '2nde C', '2009-05-09'),
  ('Hélèna', 'Garcia', 'h.gar160@edu.com', '$2b$14$eUf5iZdlyWfms7DNK7hkR.RBDd8Hss6/W1vICUbJxblebekvPFcxW', '1ère STMG A', '2008-06-10');
