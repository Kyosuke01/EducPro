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
    edt_id INT PRIMARY KEY AUTO_INCREMENT,
    class_name VARCHAR(100) NOT NULL,
    teacher_f_name VARCHAR(100) NOT NULL,
    teacher_l_name VARCHAR(100) NOT NULL,
    topic_name VARCHAR(100) NOT NULL,
    room_name VARCHAR(50) NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL
) DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des présences (Absences / Retards)
CREATE TABLE IF NOT EXISTS ATTENDANCE (
  attendance_id INT PRIMARY KEY AUTO_INCREMENT,
  student_id INT NOT NULL,
    edt_id INT,
    date_attendance DATE NOT NULL,
    status ENUM('present', 'absent', 'late') DEFAULT 'present',
    justified BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (student_id) REFERENCES Student(student_id) ON DELETE CASCADE,
    FOREIGN KEY (edt_id) REFERENCES EDT(edt_id) ON DELETE SET NULL
) DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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