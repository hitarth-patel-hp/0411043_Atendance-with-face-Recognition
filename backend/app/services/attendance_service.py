from models.attendance import Attendance
from models.user import User
from datetime import datetime

class AttendanceService:
    @staticmethod
    def mark_attendance(user_id, location):
        """Mark user attendance"""
        try:
            Attendance.log_checkin(user_id, location)
            user = User.get_by_id(user_id)
            return {
                'success': True,
                'user_name': user[1],  # user[1] is name
                'timestamp': datetime.now().isoformat(),
                'location': location
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_today_attendance():
        """Get today's attendance records"""
        records = Attendance.get_today_records()
        return [
            {
                'user_id': r[0],
                'name': r[1],
                'check_in_time': r[2],
                'location': r[3]
            }
            for r in records
        ]