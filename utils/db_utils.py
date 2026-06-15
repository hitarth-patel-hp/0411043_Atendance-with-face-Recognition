import sqlite3
import os
import pickle as pkl
import hashlib
from datetime import datetime, date


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "attendance.db")
DATASET_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "dataset")


def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            employee_id TEXT UNIQUE NOT NULL,
            email TEXT,
            department TEXT,
            semester TEXT,
            year TEXT,
            face_encodings BLOB,
            profile_photo BLOB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date DATE NOT NULL,
            check_in_time TIMESTAMP,
            check_out_time TIMESTAMP,
            location TEXT DEFAULT 'Lecture Hall',
            status TEXT DEFAULT 'Present',
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            teacher_id TEXT UNIQUE NOT NULL,
            email TEXT,
            department TEXT,
            password TEXT NOT NULL,
            is_approved INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()

    # Migrate existing DB: add new columns if they don't exist
    for col, default in [("semester", "''"), ("year", "''"), ("face_encodings", "NULL"), ("profile_photo", "NULL"), ("password", "''")]:
        try:
            c.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT DEFAULT {default}")
            conn.commit()
        except sqlite3.OperationalError:
            pass  # column already exists

    # Set default password = hash(roll_no) for students who don't have one yet
    c.execute("SELECT id, employee_id FROM users WHERE password IS NULL OR password = ''")
    for row in c.fetchall():
        c.execute("UPDATE users SET password=? WHERE id=?", (_hash(row["employee_id"]), row["id"]))
    conn.commit()

    conn.close()


# ── Users ──────────────────────────────────────────────────────────────────────

def create_user(name, employee_id, email="", department="", semester="", year="", password=None):
    conn = get_connection()
    c = conn.cursor()
    hashed = _hash(password) if password else _hash(employee_id)
    try:
        c.execute(
            "INSERT INTO users (name, employee_id, email, department, semester, year, password) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, employee_id, email, department, semester, year, hashed),
        )
        conn.commit()
        return c.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def verify_student_login(roll_no: str, password: str) -> dict | None:
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT id, name, employee_id, department, semester, year FROM users WHERE employee_id=? AND password=? AND is_active=1",
        (roll_no, _hash(password)),
    )
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def get_student_attendance(user_id: int) -> list:
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """
        SELECT date, check_in_time, check_out_time, location, status
        FROM attendance
        WHERE user_id=?
        ORDER BY date DESC, check_in_time DESC
        """,
        (user_id,),
    )
    records = [dict(row) for row in c.fetchall()]
    conn.close()
    return records


def get_all_users():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, name, employee_id, email, department, semester, year, created_at, is_active FROM users WHERE is_active=1 ORDER BY name")
    users = [dict(row) for row in c.fetchall()]
    conn.close()
    return users


def get_user_by_id(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, name, employee_id, email, department, semester, year, created_at FROM users WHERE id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def delete_user(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET is_active=0 WHERE id=?", (user_id,))
    conn.commit()
    conn.close()


# ── Face encodings (stored as BLOB in users table) ─────────────────────────────

def save_face_encodings_db(user_id: int, encodings_list: list):
    """Serialize and persist face encodings directly in the users table."""
    conn = get_connection()
    c = conn.cursor()
    blob = sqlite3.Binary(pkl.dumps(encodings_list))
    c.execute("UPDATE users SET face_encodings=? WHERE id=?", (blob, user_id))
    conn.commit()
    conn.close()


def load_face_encodings_db(user_id: int) -> list:
    """Load face encodings for a single user from DB."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT face_encodings FROM users WHERE id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row and row["face_encodings"]:
        return pkl.loads(bytes(row["face_encodings"]))
    return []


def load_all_face_encodings_db() -> dict:
    """Load {user_id: [encoding, ...]} for all active enrolled students."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, face_encodings FROM users WHERE is_active=1 AND face_encodings IS NOT NULL")
    result = {}
    for row in c.fetchall():
        blob = row["face_encodings"]
        if blob:
            encs = pkl.loads(bytes(blob))
            if encs:
                result[row["id"]] = encs
    conn.close()
    return result


def delete_face_encodings_db(user_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET face_encodings=NULL WHERE id=?", (user_id,))
    conn.commit()
    conn.close()


# ── Profile photo ──────────────────────────────────────────────────────────────


def save_dataset_photos(user_id: int, employee_id: str, name: str, photos: list[bytes]):
    """Save all training photo bytes to data/dataset/<employee_id>_<name>/photo_N.jpg."""
    safe_name = name.replace(" ", "_")
    folder = os.path.join(DATASET_DIR, f"{employee_id}_{safe_name}")
    os.makedirs(folder, exist_ok=True)
    for i, photo_bytes in enumerate(photos, start=1):
        path = os.path.join(folder, f"photo_{i}.jpg")
        with open(path, "wb") as f:
            f.write(photo_bytes)
    return folder


def save_profile_photo(user_id: int, photo_bytes: bytes):
    """Store JPEG photo bytes for a user."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET profile_photo=? WHERE id=?", (sqlite3.Binary(photo_bytes), user_id))
    conn.commit()
    conn.close()


def get_profile_photo(user_id: int) -> bytes | None:
    """Return raw JPEG bytes for the student's profile photo, or None."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT profile_photo FROM users WHERE id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row and row["profile_photo"]:
        return bytes(row["profile_photo"])
    return None


# ── Attendance ─────────────────────────────────────────────────────────────────

def mark_checkin(user_id, location="Lecture Hall"):
    """Returns ('success'|'already_in'|'already_done', record_id).

    One attendance record per student per day regardless of location.
    """
    conn = get_connection()
    c = conn.cursor()
    today = date.today().isoformat()
    now = datetime.now().isoformat()

    c.execute(
        "SELECT id, check_out_time FROM attendance WHERE user_id=? AND date=?",
        (user_id, today),
    )
    existing = c.fetchone()

    if existing:
        conn.close()
        return ("already_in" if existing["check_out_time"] is None else "already_done"), None

    c.execute(
        "INSERT INTO attendance (user_id, date, check_in_time, location) VALUES (?, ?, ?, ?)",
        (user_id, today, now, location),
    )
    conn.commit()
    record_id = c.lastrowid
    conn.close()
    return "success", record_id


def mark_checkout(user_id, location=None):
    conn = get_connection()
    c = conn.cursor()
    today = date.today().isoformat()
    now = datetime.now().isoformat()

    if location:
        c.execute(
            "SELECT id FROM attendance WHERE user_id=? AND date=? AND location=? AND check_out_time IS NULL",
            (user_id, today, location),
        )
    else:
        c.execute(
            "SELECT id FROM attendance WHERE user_id=? AND date=? AND check_out_time IS NULL ORDER BY check_in_time DESC LIMIT 1",
            (user_id, today),
        )
    row = c.fetchone()
    if not row:
        conn.close()
        return False

    c.execute("UPDATE attendance SET check_out_time=? WHERE id=?", (now, row["id"]))
    conn.commit()
    conn.close()
    return True


def get_today_attendance():
    conn = get_connection()
    c = conn.cursor()
    today = date.today().isoformat()
    c.execute(
        """
        SELECT a.id, a.user_id, u.name, u.employee_id, u.department,
               a.check_in_time, a.check_out_time, a.location, a.status
        FROM attendance a
        JOIN users u ON a.user_id = u.id
        WHERE a.date = ?
        ORDER BY a.check_in_time DESC
        """,
        (today,),
    )
    records = [dict(row) for row in c.fetchall()]
    conn.close()
    return records


def get_attendance_by_date_range(start_date, end_date, user_id=None):
    conn = get_connection()
    c = conn.cursor()

    query = """
        SELECT a.id, u.name, u.employee_id, u.department,
               a.date, a.check_in_time, a.check_out_time, a.location, a.status
        FROM attendance a
        JOIN users u ON a.user_id = u.id
        WHERE a.date BETWEEN ? AND ?
    """
    params = [start_date, end_date]

    if user_id:
        query += " AND a.user_id = ?"
        params.append(user_id)

    query += " ORDER BY a.date DESC, a.check_in_time DESC"
    c.execute(query, params)
    records = [dict(row) for row in c.fetchall()]
    conn.close()
    return records


# ── Teachers ───────────────────────────────────────────────────────────────────

def create_teacher(name, teacher_id, email="", department="", password=None):
    conn = get_connection()
    c = conn.cursor()
    hashed = _hash(password) if password else _hash(teacher_id)
    try:
        c.execute(
            "INSERT INTO teachers (name, teacher_id, email, department, password) VALUES (?, ?, ?, ?, ?)",
            (name, teacher_id, email, department, hashed),
        )
        conn.commit()
        return c.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def verify_teacher_login(teacher_id: str, password: str) -> dict | None:
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT id, name, teacher_id, email, department FROM teachers WHERE teacher_id=? AND password=? AND is_approved=1 AND is_active=1",
        (teacher_id, _hash(password)),
    )
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def is_teacher_pending(teacher_id: str) -> bool:
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT id FROM teachers WHERE teacher_id=? AND is_approved=0 AND is_active=1",
        (teacher_id,),
    )
    row = c.fetchone()
    conn.close()
    return row is not None


def get_pending_teachers() -> list:
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT id, name, teacher_id, email, department, created_at FROM teachers WHERE is_approved=0 AND is_active=1 ORDER BY created_at DESC"
    )
    result = [dict(row) for row in c.fetchall()]
    conn.close()
    return result


def get_all_teachers() -> list:
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT id, name, teacher_id, email, department, is_approved, created_at FROM teachers WHERE is_active=1 ORDER BY name"
    )
    result = [dict(row) for row in c.fetchall()]
    conn.close()
    return result


def approve_teacher(teacher_db_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE teachers SET is_approved=1 WHERE id=?", (teacher_db_id,))
    conn.commit()
    conn.close()


def reject_teacher(teacher_db_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE teachers SET is_active=0 WHERE id=?", (teacher_db_id,))
    conn.commit()
    conn.close()


def get_attendance_summary(year, month):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """
        SELECT u.name, u.department, COUNT(a.id) AS days_present
        FROM users u
        LEFT JOIN attendance a
            ON u.id = a.user_id
            AND strftime('%Y', a.date) = ?
            AND strftime('%m', a.date) = ?
        WHERE u.is_active = 1
        GROUP BY u.id
        ORDER BY u.name
        """,
        (str(year), f"{month:02d}"),
    )
    records = [dict(row) for row in c.fetchall()]
    conn.close()
    return records
