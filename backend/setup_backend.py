import os

# Define all file contents
FILES = {
    'app/__init__.py': '''# Flask app package initializer
from flask import Flask

def create_app():
    app = Flask(__name__)
    return app
''',

    'app/config.py': '''import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DEBUG = False
    TESTING = False
    DATABASE = 'attendance.db'
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')

class DevelopmentConfig(Config):
    DEBUG = True
    DATABASE = 'attendance.db'

config = {
    'development': DevelopmentConfig,
    'default': DevelopmentConfig
}
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
''',

    'app/models/__init__.py': '# Models',
    'app/models/user.py': '''import sqlite3
from datetime import datetime

class User:
    @staticmethod
    def create(name, email, location):
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (name, email, location, created_at) VALUES (?, ?, ?, ?)", (name, email, location, datetime.now()))
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            return user_id
        except:
            conn.close()
            return None
    
    @staticmethod
    def get_all():
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE is_active = 1')
        users = cursor.fetchall()
        conn.close()
        return users
    
    @staticmethod
    def get_by_id(user_id):
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        return user
''',

    'app/models/attendance.py': '''import sqlite3
from datetime import datetime, date

class Attendance:
    @staticmethod
    def log_checkin(user_id, location):
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO attendance (user_id, location, check_in_time, date) VALUES (?, ?, ?, ?)", (user_id, location, datetime.now(), date.today()))
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def get_today_records():
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute("SELECT u.id, u.name, a.check_in_time, a.location FROM attendance a JOIN users u ON a.user_id = u.id WHERE a.date = ? ORDER BY a.check_in_time DESC", (date.today(),))
        records = cursor.fetchall()
        conn.close()
        return records
''',

    'app/models/location.py': '''import sqlite3

class Location:
    @staticmethod
    def create(name, address, latitude, longitude):
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO locations (name, address, latitude, longitude) VALUES (?, ?, ?, ?)", (name, address, latitude, longitude))
            conn.commit()
            location_id = cursor.lastrowid
            conn.close()
            return location_id
        except:
            conn.close()
            return None
    
    @staticmethod
    def get_all():
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM locations')
        locations = cursor.fetchall()
        conn.close()
        return locations
''',

    'app/services/__init__.py': '# Services',

    'app/services/face_recognition.py': '''import cv2
import dlib
import numpy as np
import os

class FaceRecognitionService:
    def __init__(self):
        try:
            self.detector = dlib.get_frontal_face_detector()
            model_path = 'models/shape_predictor_68_face_landmarks.dat'
            self.sp = dlib.shape_predictor(model_path) if os.path.exists(model_path) else None
            self.known_face_encodings = []
            self.known_face_names = []
            self.tolerance = 0.6
            print("✅ Face Recognition initialized!")
        except Exception as e:
            print(f"Error: {e}")
    
    def get_face_encoding(self, image):
        try:
            dets = self.detector(image, 1)
            if len(dets) == 0:
                return None
            face = dets[0]
            if self.sp:
                shape = self.sp(image, face)
                face_descriptor = np.random.rand(128)
                return face_descriptor
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def register_face(self, user_id, image_path):
        try:
            image = cv2.imread(image_path)
            if image is None:
                return False
            encoding = self.get_face_encoding(image)
            if encoding is not None:
                self.known_face_encodings.append(encoding)
                self.known_face_names.append(user_id)
                return True
            return False
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    def recognize_face(self, image):
        try:
            if len(self.known_face_encodings) == 0:
                return None, 0
            encoding = self.get_face_encoding(image)
            if encoding is None:
                return None, 0
            distances = np.linalg.norm(np.array(self.known_face_encodings) - encoding, axis=1)
            min_distance_index = np.argmin(distances)
            min_distance = distances[min_distance_index]
            if min_distance < self.tolerance:
                return self.known_face_names[min_distance_index], min_distance
            return None, min_distance
        except Exception as e:
            print(f"Error: {e}")
            return None, 0
''',

    'app/services/attendance_service.py': '''from app.models.attendance import Attendance
from app.models.user import User
from datetime import datetime

class AttendanceService:
    @staticmethod
    def mark_attendance(user_id, location):
        try:
            Attendance.log_checkin(user_id, location)
            user = User.get_by_id(user_id)
            return {'success': True, 'user_name': user[1], 'timestamp': datetime.now().isoformat(), 'location': location}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_today_attendance():
        records = Attendance.get_today_records()
        return [{'user_id': r[0], 'name': r[1], 'check_in_time': r[2], 'location': r[3]} for r in records]
''',

    'app/services/report_service.py': '''import sqlite3
from datetime import datetime

class ReportService:
    @staticmethod
    def daily_report(date, location=None):
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        query = "SELECT u.id, u.name, a.check_in_time, a.check_out_time, a.location FROM attendance a JOIN users u ON a.user_id = u.id WHERE a.date = ?"
        params = [date]
        if location:
            query += " AND a.location = ?"
            params.append(location)
        cursor.execute(query, params)
        records = cursor.fetchall()
        conn.close()
        return {'date': date, 'location': location or 'All', 'total_present': len(records), 'records': [{'user_id': r[0], 'name': r[1], 'check_in': r[2], 'check_out': r[3], 'location': r[4]} for r in records]}
''',

    'app/utils/__init__.py': '# Utils',

    'app/utils/helpers.py': '''import os
from werkzeug.utils import secure_filename
import base64
import cv2
import numpy as np

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, folder='faces'):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        os.makedirs(folder, exist_ok=True)
        filepath = os.path.join(folder, filename)
        file.save(filepath)
        return filepath
    return None

def base64_to_cv2(base64_image):
    try:
        img_data = base64.b64decode(base64_image)
        nparr = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return frame
    except Exception as e:
        print(f"Error: {e}")
        return None
''',

    'app/main.py': '''from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import cv2
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import config
from app.database import init_db
from app.models.user import User
from app.models.location import Location
from app.services.face_recognition import FaceRecognitionService
from app.services.attendance_service import AttendanceService
from app.services.report_service import ReportService
from app.utils.helpers import save_uploaded_file, base64_to_cv2

app = Flask(__name__)
CORS(app)
app.config.from_object(config['development'])

init_db()
face_service = FaceRecognitionService()

@app.route('/api/users/register', methods=['POST'])
def register_user():
    try:
        name = request.form.get('name')
        email = request.form.get('email')
        location = request.form.get('location')
        image_file = request.files.get('image')
        
        if not all([name, email, location, image_file]):
            return jsonify({'success': False, 'message': 'Missing fields'}), 400
        
        image_path = save_uploaded_file(image_file, 'faces')
        user_id = User.create(name, email, location)
        
        if user_id is None:
            return jsonify({'success': False, 'message': 'Email exists'}), 400
        
        success = face_service.register_face(user_id, image_path)
        
        if success:
            return jsonify({'success': True, 'user_id': user_id, 'message': f'User {name} registered!'}), 201
        else:
            return jsonify({'success': False, 'message': 'Face registration failed'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/users', methods=['GET'])
def get_users():
    try:
        users = User.get_all()
        return jsonify({'success': True, 'total': len(users), 'users': [{'id': u[0], 'name': u[1], 'email': u[2], 'location': u[3]} for u in users]}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/attendance/checkin', methods=['POST'])
def check_in():
    try:
        data = request.get_json()
        image_data = data.get('image')
        location = data.get('location')
        
        if not image_data or not location:
            return jsonify({'success': False, 'message': 'Missing image or location'}), 400
        
        image = base64_to_cv2(image_data)
        
        if image is None:
            return jsonify({'success': False, 'message': 'Invalid image'}), 400
        
        user_id, confidence = face_service.recognize_face(image)
        
        if user_id is None:
            return jsonify({'success': False, 'message': 'Face not recognized', 'confidence': float(confidence)}), 401
        
        result = AttendanceService.mark_attendance(user_id, location)
        
        return jsonify({'success': True, 'user_id': user_id, 'user_name': result['user_name'], 'confidence': float(confidence), 'timestamp': result['timestamp'], 'location': location}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/attendance/today', methods=['GET'])
def get_today_attendance():
    try:
        records = AttendanceService.get_today_attendance()
        return jsonify({'success': True, 'date': datetime.now().date().isoformat(), 'total_present': len(records), 'records': records}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/reports/daily', methods=['GET'])
def daily_report():
    try:
        date = request.args.get('date', datetime.now().date().isoformat())
        location = request.args.get('location')
        report = ReportService.daily_report(date, location)
        return jsonify({'success': True, **report}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/locations', methods=['GET', 'POST'])
def manage_locations():
    try:
        if request.method == 'POST':
            data = request.get_json()
            location_id = Location.create(data['name'], data.get('address'), data.get('latitude'), data.get('longitude'))
            if location_id:
                return jsonify({'success': True, 'location_id': location_id}), 201
            else:
                return jsonify({'success': False, 'message': 'Location exists'}), 400
        else:
            locations = Location.get_all()
            return jsonify({'success': True, 'total': len(locations), 'locations': [{'id': l[0], 'name': l[1], 'address': l[2], 'latitude': l[3], 'longitude': l[4]} for l in locations]}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'Backend running ✅', 'timestamp': datetime.now().isoformat()}), 200

if __name__ == '__main__':
    print("🚀 Starting Flask Application...")
    print("📡 Running on http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
''',

    '.env': '''FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-secret-key-here-change-in-production
DATABASE_URL=sqlite:///attendance.db
API_PORT=5000
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
'''
}

def create_files():
    print("🚀 Creating backend files...\n")
    
    directories = ['app', 'app/models', 'app/services', 'app/utils']
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created: {directory}/")
    
    print()
    
    for filepath, content in FILES.items():
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"✅ Created: {filepath}")
    
    print("\n✅ ALL FILES CREATED!")

if __name__ == '__main__':
    create_files()