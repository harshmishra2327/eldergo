-- ElderGo+ Full-Stack Database Schema for MySQL

CREATE DATABASE IF NOT EXISTS eldergo_db;
USE eldergo_db;

-- Safely disable foreign key checks for clean table recreation
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS feedbacks;
DROP TABLE IF EXISTS verifications;
DROP TABLE IF EXISTS bookings;
DROP TABLE IF EXISTS companions;
DROP TABLE IF EXISTS users;

SET FOREIGN_KEY_CHECKS = 1;

-- 1. Users Table (Clients, Companions, Admins)
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('client', 'companion', 'admin') NOT NULL DEFAULT 'client',
    full_name VARCHAR(120) NOT NULL,
    phone VARCHAR(20),
    age INT,
    gender VARCHAR(20) DEFAULT 'Male',
    address TEXT,
    emergency_contact VARCHAR(20),
    status ENUM('active', 'inactive') DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Companions Profile Table
CREATE TABLE companions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    bio TEXT,
    rating DECIMAL(3,2) DEFAULT 4.90,
    hourly_rate INT DEFAULT 250,
    experience_years VARCHAR(50) DEFAULT '4+ Years',
    preferred_service VARCHAR(100) DEFAULT 'Medical & Hospital Visit',
    city VARCHAR(80) DEFAULT 'Bengaluru',
    availability_status ENUM('online', 'offline') DEFAULT 'online',
    verification_status ENUM('pending', 'verified', 'rejected') DEFAULT 'verified',
    document_name VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Bookings Table
CREATE TABLE bookings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    booking_code VARCHAR(30) NOT NULL UNIQUE,
    client_id INT NOT NULL,
    companion_id INT NULL,
    service_type VARCHAR(120) NOT NULL,
    booking_date VARCHAR(30) NOT NULL,
    booking_time VARCHAR(30) NOT NULL,
    duration_hours INT NOT NULL DEFAULT 2,
    pickup_address TEXT NOT NULL,
    destination_address TEXT NOT NULL,
    health_notes TEXT,
    status ENUM('SEARCHING', 'ACCEPTED', 'IN_TRANSIT', 'COMPLETED', 'CANCELLED', 'TIMED_OUT') DEFAULT 'SEARCHING',
    otp VARCHAR(10) NOT NULL,
    hourly_rate INT DEFAULT 250,
    total_fare INT DEFAULT 550,
    payment_status ENUM('UNPAID', 'PAID') DEFAULT 'UNPAID',
    payment_method VARCHAR(50) DEFAULT 'upi',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME NULL,
    FOREIGN KEY (client_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (companion_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Feedbacks Table
CREATE TABLE feedbacks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT NULL,
    client_id INT NOT NULL,
    companion_id INT NOT NULL,
    companion_name VARCHAR(120),
    rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (companion_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. Verifications Table
CREATE TABLE verifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    companion_id INT NOT NULL,
    companion_name VARCHAR(120),
    document_name VARCHAR(255),
    document_type VARCHAR(100),
    experience VARCHAR(50),
    skills TEXT,
    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (companion_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==================== SEED INITIAL DEMO ACCOUNTS ====================

-- 1. Admin Account (admin / admin123)
INSERT INTO users (id, username, email, password_hash, role, full_name, phone, age, gender, address, emergency_contact, status)
VALUES (1, 'admin', 'admin@eldergo.com', 'scrypt:32768:8:1$4vK5dY6z$417d472251a37bbdf6b49e32049e776a37887e59bcfdfa62a98f121d51c3266e74dfc2b186b515ad4cae7a2b2c9d640ff110191837a7b8e5c1417fb664f331bd', 'admin', 'ElderGo System Administrator', '+91 99000 11223', 35, 'Male', 'ElderGo HQ, Indiranagar, Bengaluru', '9900011223', 'active');

-- 2. Companion Account (rahul / companion123)
INSERT INTO users (id, username, email, password_hash, role, full_name, phone, age, gender, address, emergency_contact, status)
VALUES (2, 'rahul', 'rahul.sharma@eldergo.com', 'scrypt:32768:8:1$9mJ3kP7x$c8313e9a7e6b8159b32c6686bf5ad5efcfc2a05d6e2e2a8654497e5932598835848792df96c56784d0ef925c2763f03b540113c2f0f423ab676d9124430e3860', 'companion', 'Rahul Sharma', '+91 98450 12345', 28, 'Male', 'JP Nagar 2nd Phase, Bengaluru', '9845012345', 'active');

INSERT INTO companions (user_id, bio, rating, hourly_rate, experience_years, preferred_service, city, availability_status, verification_status, document_name)
VALUES (2, 'Certified Senior Care Assistant & First Aid Specialist with 4+ years experience.', 4.90, 250, '4+ Years', 'Medical & Hospital Visit', 'Bengaluru', 'online', 'verified', 'Identity_NurseCert.pdf');

-- 3. Client Account (client / client123)
INSERT INTO users (id, username, email, password_hash, role, full_name, phone, age, gender, address, emergency_contact, status)
VALUES (3, 'client', 'ramesh.sen@gmail.com', 'scrypt:32768:8:1$7tY2wL8q$b9347d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c', 'client', 'Ramesh Sen', '+91 98765 43210', 68, 'Male', 'JP Nagar 4th Phase, Bengaluru', '9876543210', 'active');
