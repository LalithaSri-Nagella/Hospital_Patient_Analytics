-- Hospital Patient Data Analysis System
-- Database Schema for MySQL 8.0+

CREATE DATABASE IF NOT EXISTS hospital_analytics
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE hospital_analytics;

-- 1. Departments Table
CREATE TABLE IF NOT EXISTS departments (
    department_id INT AUTO_INCREMENT PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 2. Patients Table (Fictional demographic data only)
CREATE TABLE IF NOT EXISTS patients (
    patient_id INT AUTO_INCREMENT PRIMARY KEY,
    age_group VARCHAR(20) NOT NULL,
    gender VARCHAR(20) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_patient_age (age_group),
    INDEX idx_patient_gender (gender)
) ENGINE=InnoDB;

-- 3. Visits Table
CREATE TABLE IF NOT EXISTS visits (
    visit_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    department_id INT NOT NULL,
    visit_date DATE NOT NULL,
    visit_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_visit_patient FOREIGN KEY (patient_id) 
        REFERENCES patients(patient_id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
    CONSTRAINT fk_visit_department FOREIGN KEY (department_id) 
        REFERENCES departments(department_id) 
        ON DELETE RESTRICT 
        ON UPDATE CASCADE,
    INDEX idx_visit_date (visit_date),
    INDEX idx_visit_patient (patient_id),
    INDEX idx_visit_department (department_id),
    INDEX idx_visit_type (visit_type)
) ENGINE=InnoDB;
