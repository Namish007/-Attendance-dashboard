-- ============================================================
-- attendance_system.sql
-- Run this in phpMyAdmin or MySQL CLI to set up the database
-- ============================================================

CREATE DATABASE IF NOT EXISTS attendance_system
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE attendance_system;

-- ─────────────────────────────────────────────
-- Table: students
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS students (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100)  NOT NULL,
    roll_no     VARCHAR(50)   NOT NULL UNIQUE,
    image_path  VARCHAR(255)  DEFAULT NULL,
    created_at  TIMESTAMP     DEFAULT CURRENT_TIMESTAMP
);

-- ─────────────────────────────────────────────
-- Table: attendance
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS attendance (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    student_id  INT           NOT NULL,
    date        DATE          NOT NULL,
    time        TIME          NOT NULL,
    status      ENUM('Present','Absent') DEFAULT 'Present',
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    -- Prevent duplicate attendance on the same day
    UNIQUE KEY unique_attendance (student_id, date)
);

-- ─────────────────────────────────────────────
-- Sample dummy data
-- ─────────────────────────────────────────────
INSERT INTO students (name, roll_no, image_path) VALUES
  ('Rupesh Kumar Singh',  '2401330100295', 'dataset/2401330100295'),
  ('Namish Srivastava',   '2401330100231', 'dataset/2401330100231'),
  ('Rishabh Kumar',       '2401330100278', 'dataset/2401330100278'),
  ('Priya Sharma',        '2401330100101', 'dataset/2401330100101'),
  ('Ankit Verma',         '2401330100102', 'dataset/2401330100102');
