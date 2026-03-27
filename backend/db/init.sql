CREATE TABLE Student (
  student_id INT PRIMARY KEY AUTO_INCREMENT,
  n_admin_id VARCHAR(100) UNIQUE,
  student_name VARCHAR(100),
  mail_student VARCHAR(255),
  password VARCHAR(255),
  class_id INT /* FOREIGN KEY */,
  dob DATETIME
);

CREATE TABLE Teacher (
  teacher_id INT PRIMARY KEY AUTO_INCREMENT,
  teacher_name VARCHAR(100),
  topic_id INT /* FOREIGN KEY */
);

CREATE TABLE Room (
  room_id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(50)
);

CREATE TABLE Topic (
  topic_id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100) UNIQUE,
  teacher_id INT /* FOREIGN KEY */,
  class_id INT /* FOREIGN KEY */
);

CREATE TABLE Class (
  class_id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100) UNIQUE,
  student_id INT /* FOREIGN KEY */,
  teacher_id INT /* FOREIGN KEY */
);

CREATE TABLE Grade (
  grade_id INT PRIMARY KEY AUTO_INCREMENT,
  grade FLOAT,
  student_id INT /* FOREIGN KEY */,
  topic_id INT /* FOREIGN KEY */
);

CREATE TABLE EDT (
  edt_id INT PRIMARY KEY AUTO_INCREMENT,
  topic_id INT /* FOREIGN KEY */,
  room_id INT /* FOREIGN KEY */,
  teacher_id INT /* FOREIGN KEY */,
  class_id INT /* FOREIGN KEY */,
  start_time DATETIME,
  end_time DATETIME
);

CREATE TABLE Attendance (
  attendance_id INT PRIMARY KEY AUTO_INCREMENT,
  late INT,
  absent INT,
  student_id INT /* FOREIGN KEY */,
  topic_id INT /* FOREIGN KEY */
);

CREATE TABLE TICKET (
  ticket_id INT PRIMARY KEY AUTO_INCREMENT,
  msg_content VARCHAR(255),
  teacher_id INT /* FOREIGN KEY */,
  student_id INT /* FOREIGN KEY */
);