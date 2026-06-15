import sqlite3
from datetime import datetime, date

class Attendance:
    @staticmethod
    def log_checkin(user_id, location):
        """Log user check-in"""
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO attendance (user_id, location, check_in_time, date)
            VALUES (?, ?, ?, ?)
        ''', (user_id, location, datetime.now(), date.today()))
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def log_checkout(user_id):
        """Log user check-out"""
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE attendance 
            SET check_out_time = ? 
            WHERE user_id = ? AND date = ? AND check_out_time IS NULL
        ''', (datetime.now(), user_id, date.today()))
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def get_today_records():
        """Get today's attendance"""
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.id, u.name, a.check_in_time, a.location 
            FROM attendance a
            JOIN users u ON a.user_id = u.id
            WHERE a.date = ?
            ORDER BY a.check_in_time DESC
        ''', (date.today(),))
        records = cursor.fetchall()
        conn.close()
        return records