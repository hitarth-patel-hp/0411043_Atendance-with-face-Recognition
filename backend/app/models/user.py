# app/models/user.py
from datetime import datetime
import sqlite3

class User:
    @staticmethod
    def create_table():
        conn = sqlite3.connect('attendance.db')
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                face_encoding BLOB,
                location TEXT,
                created_at TIMESTAMP,
                is_active BOOLEAN
            )
        ''')
        conn.commit()
        conn.close()

# app/models/attendance.py
class Attendance:
    @staticmethod
    def create_table():
        conn = sqlite3.connect('attendance.db')
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                location TEXT,
                check_in_time TIMESTAMP,
                check_out_time TIMESTAMP,
                date DATE,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        conn.commit()
        conn.close()

# app/models/location.py
class Location:
    @staticmethod
    def create_table():
        conn = sqlite3.connect('attendance.db')
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE,
                address TEXT,
                latitude REAL,
                longitude REAL
            )
        ''')
        conn.commit()
        conn.close()