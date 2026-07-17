-- Run this once if you'd rather create the DB by hand than let
-- SQLAlchemy's db.create_all() do it automatically on first run.

CREATE DATABASE IF NOT EXISTS skillgap_db
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE skillgap_db;

CREATE TABLE IF NOT EXISTS analysis (
    id INT AUTO_INCREMENT PRIMARY KEY,
    resume_text TEXT NOT NULL,
    jd_text TEXT NOT NULL,
    resume_skills TEXT NOT NULL,
    jd_skills TEXT NOT NULL,
    matched_skills TEXT NOT NULL,
    missing_skills TEXT NOT NULL,
    match_percentage FLOAT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
