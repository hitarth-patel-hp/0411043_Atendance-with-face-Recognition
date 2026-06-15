import os

# Create all files automatically
files = {
    'app/__init__.py': 'print("Flask app initialized")',
    'app/config.py': '''import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DEBUG = True
    DATABASE = 'attendance.db'
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
''',
    'app/database.py': '''import sqlite3
from datetime import datetime

DATABASE = 'attendance.db'

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            location TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            location TEXT,
            check_in_time TIMESTAMP,
            check_out_time TIMESTAMP,
            date DATE DEFAULT CURRENT_DATE,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            address TEXT,
            latitude REAL,
            longitude REAL
        )
    """)
    
    db.commit()
    db.close()
    print("✅ Database initialized!")

if __name__ == '__main__':
    init_db()
'''
}

# Create directories
os.makedirs('app/models', exist_ok=True)
os.makedirs('app/services', exist_ok=True)
os.makedirs('app/utils', exist_ok=True)

# Create files
for filepath, content in files.items():
    with open(filepath, 'w') as f:
        f.write(content)
    print(f"✅ Created {filepath}")

print("\n✅ All files created successfully!")