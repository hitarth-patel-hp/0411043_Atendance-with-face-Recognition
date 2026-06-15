import sqlite3
from datetime import datetime
import os

DATABASE = 'attendance.db'

def get_db():
    """Get database connection"""
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    """Initialize database with tables"""
    db = get_db()
    cursor = db.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            location TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    
    # Attendance table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            location TEXT,
            check_in_time TIMESTAMP,
            check_out_time TIMESTAMP,
            date DATE DEFAULT CURRENT_DATE,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    # Locations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            address TEXT,
            latitude REAL,
            longitude REAL
        )
    ''')
    
    db.commit()
    db.close()
    print("✅ Database initialized successfully!")

if __name__ == '__main__':
    init_db()