import sqlite3
from datetime import datetime, timedelta

class ReportService:
    @staticmethod
    def daily_report(date, location=None):
        """Generate daily attendance report"""
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        query = '''
            SELECT u.id, u.name, a.check_in_time, a.check_out_time, a.location
            FROM attendance a
            JOIN users u ON a.user_id = u.id
            WHERE a.date = ?
        '''
        params = [date]
        
        if location:
            query += ' AND a.location = ?'
            params.append(location)
        
        query += ' ORDER BY a.check_in_time DESC'
        cursor.execute(query, params)
        records = cursor.fetchall()
        conn.close()
        
        return {
            'date': date,
            'location': location or 'All',
            'total_present': len(records),
            'records': [
                {
                    'user_id': r[0],
                    'name': r[1],
                    'check_in': r[2],
                    'check_out': r[3],
                    'location': r[4]
                }
                for r in records
            ]
        }
    
    @staticmethod
    def monthly_report(year, month):
        """Generate monthly report"""
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.name, COUNT(*) as days_present
            FROM attendance a
            JOIN users u ON a.user_id = u.id
            WHERE strftime('%Y-%m', a.date) = ?
            GROUP BY u.id
            ORDER BY days_present DESC
        ''', (f'{year:04d}-{month:02d}',))
        records = cursor.fetchall()
        conn.close()
        
        return {
            'year': year,
            'month': month,
            'records': [{'name': r[0], 'days_present': r[1]} for r in records]
        }