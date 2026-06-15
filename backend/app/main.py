
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import cv2
import os

from config import config
from database import init_db
from models.user import User
from models.location import Location
from services.face_recognition import FaceRecognitionService
from services.attendance_service import AttendanceService
from services.report_service import ReportService
from utils.helpers import save_uploaded_file, base64_to_cv2

# Initialize Flask app
app = Flask(__name__)
CORS(app)
app.config.from_object(config['development'])

# Initialize database
init_db()

# Initialize face recognition service
face_service = FaceRecognitionService()

# ==================== USERS ROUTES ====================

@app.route('/api/users/register', methods=['POST'])
def register_user():
    """Register new user with face"""
    try:
        name = request.form.get('name')
        email = request.form.get('email')
        location = request.form.get('location')
        image_file = request.files['image']
        
        if not all([name, email, location, image_file]):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        # Save image
        image_path = save_uploaded_file(image_file, 'faces')
        
        # Create user in database
        user_id = User.create(name, email, location)
        
        if user_id is None:
            return jsonify({'success': False, 'message': 'Email already exists'}), 400
        
        # Register face
        success = face_service.register_face(user_id, image_path)
        
        if success:
            return jsonify({
                'success': True,
                'user_id': user_id,
                'message': f'User {name} registered successfully!'
            }), 201
        else:
            return jsonify({'success': False, 'message': 'Face registration failed'}), 400
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/users', methods=['GET'])
def get_users():
    """Get all registered users"""
    try:
        users = User.get_all()
        return jsonify({
            'success': True,
            'total': len(users),
            'users': [
                {'id': u[0], 'name': u[1], 'email': u[2], 'location': u[3]}
                for u in users
            ]
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== ATTENDANCE ROUTES ====================

@app.route('/api/attendance/checkin', methods=['POST'])
def check_in():
    """Mark attendance with face recognition"""
    try:
        data = request.get_json()
        image_data = data.get('image')
        location = data.get('location')
        
        if not image_data or not location:
            return jsonify({'success': False, 'message': 'Missing image or location'}), 400
        
        # Convert base64 to CV2 image
        image = base64_to_cv2(image_data)
        
        if image is None:
            return jsonify({'success': False, 'message': 'Invalid image'}), 400
        
        # Recognize face
        user_id, confidence = face_service.recognize_face(image)
        
        if user_id is None:
            return jsonify({
                'success': False,
                'message': 'Face not recognized',
                'confidence': float(confidence)
            }), 401
        
        # Mark attendance
        result = AttendanceService.mark_attendance(user_id, location)
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'user_name': result['user_name'],
            'confidence': float(confidence),
            'timestamp': result['timestamp'],
            'location': location
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/attendance/today', methods=['GET'])
def get_today_attendance():
    """Get today's attendance"""
    try:
        records = AttendanceService.get_today_attendance()
        return jsonify({
            'success': True,
            'date': datetime.now().date().isoformat(),
            'total_present': len(records),
            'records': records
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== REPORTS ROUTES ====================

@app.route('/api/reports/daily', methods=['GET'])
def daily_report():
    """Get daily attendance report"""
    try:
        date = request.args.get('date', datetime.now().date().isoformat())
        location = request.args.get('location')
        
        report = ReportService.daily_report(date, location)
        return jsonify({'success': True, **report}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/reports/monthly', methods=['GET'])
def monthly_report():
    """Get monthly attendance report"""
    try:
        year = int(request.args.get('year', datetime.now().year))
        month = int(request.args.get('month', datetime.now().month))
        
        report = ReportService.monthly_report(year, month)
        return jsonify({'success': True, **report}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== LOCATIONS ROUTES ====================

@app.route('/api/locations', methods=['GET', 'POST'])
def manage_locations():
    """Get or create locations"""
    try:
        if request.method == 'POST':
            data = request.get_json()
            location_id = Location.create(
                data['name'],
                data.get('address'),
                data.get('latitude'),
                data.get('longitude')
            )
            if location_id:
                return jsonify({'success': True, 'location_id': location_id}), 201
            else:
                return jsonify({'success': False, 'message': 'Location already exists'}), 400
        else:
            locations = Location.get_all()
            return jsonify({
                'success': True,
                'total': len(locations),
                'locations': [
                    {
                        'id': l[0],
                        'name': l[1],
                        'address': l[2],
                        'latitude': l[3],
                        'longitude': l[4]
                    }
                    for l in locations
                ]
            }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== HEALTH CHECK ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'Backend is running ✅'}), 200

if __name__ == '__main__':
    print("🚀 Starting Flask Application...")
    print("📡 Running on http://127.0.0.1:5000")
    app.run(debug=True, port=5000)