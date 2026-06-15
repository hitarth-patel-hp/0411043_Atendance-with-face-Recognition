import sqlite3

class Location:
    @staticmethod
    def create(name, address, latitude, longitude):
        """Create new location"""
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO locations (name, address, latitude, longitude)
                VALUES (?, ?, ?, ?)
            ''', (name, address, latitude, longitude))
            conn.commit()
            location_id = cursor.lastrowid
            conn.close()
            return location_id
        except sqlite3.IntegrityError:
            conn.close()
            return None
    
    @staticmethod
    def get_all():
        """Get all locations"""
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM locations')
        locations = cursor.fetchall()
        conn.close()
        return locations