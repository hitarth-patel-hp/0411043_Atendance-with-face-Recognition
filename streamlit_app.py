import io
import os
import streamlit as st
import pandas as pd
from datetime import date
from PIL import Image

from utils.db_utils import (
    init_db,
    get_today_attendance, get_all_users, load_all_face_encodings_db,
    verify_student_login, get_student_attendance, create_user,
    save_profile_photo, save_dataset_photos,
    create_teacher, verify_teacher_login, is_teacher_pending,
)
from utils.face_utils import encode_image, save_face_encodings_bulk

os.makedirs("data", exist_ok=True)
init_db()

st.set_page_config(
    page_title="Student Attendance System",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Credentials (change these) ─────────────────────────────────────────────────
_ADMIN_USER = "admin"
_ADMIN_PASS = "admin123"

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.student_info = None
    st.session_state.teacher_info = None

if "reg_encodings" not in st.session_state:
    st.session_state.reg_encodings = []
    st.session_state.reg_photos = []
    st.session_state.reg_profile = None

# ── Auth page ──────────────────────────────────────────────────────────────────
if not st.session_state.logged_in:
    st.markdown(
        "<style>[data-testid='stSidebar'] { display: none; }</style>",
        unsafe_allow_html=True,
    )
    st.markdown("""
<style>
.auth-header { text-align: center; padding: 2rem 0 1rem 0; }
.auth-header h1 { font-size: 2rem; font-weight: 700; margin-bottom: 0.25rem; }
.auth-header p { color: #888; font-size: 0.95rem; }
.auth-footer { text-align: center; color: #aaa; font-size: 11px; margin-top: 2rem; padding-bottom: 1rem; }
.switch-hint { color: #888; font-size: 0.9rem; }
</style>
<div class="auth-header">
    <h1>🎓 Student Attendance System</h1>
    <p>University Face Recognition Attendance</p>
</div>
""", unsafe_allow_html=True)

    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "login"

    _, col_main, _ = st.columns([1, 1.6, 1])
    with col_main:

        # ── LOGIN ──────────────────────────────────────────────────────────────
        if st.session_state.auth_mode == "login":
            tab_stu, tab_tea = st.tabs(["🎒 Student", "🧑‍🏫 Teacher"])

            with tab_stu:
                roll_no  = st.text_input("Roll No.", placeholder="Enter your Roll Number", key="stu_roll")
                stu_pass = st.text_input("Password", type="password",
                                         placeholder="Default = your Roll No.", key="stu_pass")
                if st.button("Log In", use_container_width=True, type="primary", key="stu_btn"):
                    student = verify_student_login(roll_no.strip(), stu_pass.strip())
                    if student:
                        st.session_state.logged_in = True
                        st.session_state.role = "student"
                        st.session_state.student_info = student
                        st.rerun()
                    else:
                        st.error("Invalid Roll No. or password.")

            with tab_tea:
                username = st.text_input("Teacher ID", placeholder="Enter your Teacher ID", key="admin_user")
                password = st.text_input("Password", type="password", placeholder="Enter password", key="admin_pass")
                if st.button("Log In", use_container_width=True, type="primary", key="admin_btn"):
                    if username == _ADMIN_USER and password == _ADMIN_PASS:
                        st.session_state.logged_in = True
                        st.session_state.role = "admin"
                        st.rerun()
                    else:
                        teacher = verify_teacher_login(username.strip(), password.strip())
                        if teacher:
                            st.session_state.logged_in = True
                            st.session_state.role = "teacher"
                            st.session_state.teacher_info = teacher
                            st.rerun()
                        elif is_teacher_pending(username.strip()):
                            st.warning("Your account is pending admin approval. Please wait.")
                        else:
                            st.error("Invalid Teacher ID or password.")

            st.divider()
            c1, c2 = st.columns([3, 2])
            with c1:
                st.markdown('<span class="switch-hint">Don\'t have an account?</span>', unsafe_allow_html=True)
            with c2:
                if st.button("Create Account →", use_container_width=True, key="go_register"):
                    st.session_state.auth_mode = "register"
                    st.rerun()

        # ── REGISTER ───────────────────────────────────────────────────────────
        else:
            tab_stu, tab_tea = st.tabs(["📝 Student Registration", "✏️ Teacher Registration"])

            with tab_stu:
                r_name  = st.text_input("Full Name *", placeholder="e.g. Rahul Sharma", key="r_name")
                r_roll  = st.text_input("Enrollment / Roll No. *", placeholder="e.g. CS2024001", key="r_roll")
                r_email = st.text_input("Email (optional)", placeholder="student@university.ac.in", key="r_email")
                r_dept  = st.text_input("Course / Department", placeholder="e.g. B.Tech Computer Science", key="r_dept")
                c1, c2 = st.columns(2)
                with c1:
                    r_sem  = st.selectbox("Semester", [f"Sem {i}" for i in range(1, 9)], key="r_sem")
                with c2:
                    r_year = st.selectbox("Year", ["1st Year", "2nd Year", "3rd Year", "4th Year"], key="r_year")
                r_pwd  = st.text_input("Choose Password *", type="password", key="r_pwd")
                r_pwd2 = st.text_input("Confirm Password *", type="password", key="r_pwd2")

                st.markdown("**Face Photos** — capture at least 3")
                photo_count = len(st.session_state.reg_encodings)
                st.progress(min(photo_count / 5, 1.0), text=f"{photo_count}/5 captured")

                cam_img = st.camera_input("Position your face clearly", key="reg_cam")
                if cam_img and photo_count < 5:
                    ca, cb = st.columns(2)
                    with ca:
                        if st.button("➕ Add Photo", type="primary", use_container_width=True, key="reg_add"):
                            img = Image.open(cam_img)
                            encoding, err = encode_image(img)
                            if err:
                                st.error(err)
                            else:
                                buf = io.BytesIO()
                                img.convert("RGB").save(buf, format="JPEG", quality=85)
                                bts = buf.getvalue()
                                st.session_state.reg_encodings.append(encoding)
                                st.session_state.reg_photos.append(bts)
                                if st.session_state.reg_profile is None:
                                    st.session_state.reg_profile = bts
                                st.success(f"Photo {photo_count + 1} captured!")
                                st.rerun()
                    with cb:
                        if st.button("Clear All", use_container_width=True, key="reg_clear"):
                            st.session_state.reg_encodings = []
                            st.session_state.reg_photos = []
                            st.session_state.reg_profile = None
                            st.rerun()
                elif photo_count >= 5:
                    st.info("Max 5 photos reached.")
                    if st.button("Clear All", key="reg_clear2"):
                        st.session_state.reg_encodings = []
                        st.session_state.reg_photos = []
                        st.session_state.reg_profile = None
                        st.rerun()

                if st.session_state.reg_profile:
                    st.image(st.session_state.reg_profile, caption="Profile preview", width=80)

                if st.button("Register Account", type="primary", use_container_width=True,
                             key="reg_btn", disabled=(photo_count < 3)):
                    if not r_name.strip():
                        st.error("Full name is required.")
                    elif not r_roll.strip():
                        st.error("Roll No. is required.")
                    elif not r_pwd:
                        st.error("Please choose a password.")
                    elif r_pwd != r_pwd2:
                        st.error("Passwords do not match.")
                    else:
                        uid = create_user(name=r_name.strip(), employee_id=r_roll.strip(),
                                          email=r_email.strip(), department=r_dept.strip(),
                                          semester=r_sem, year=r_year, password=r_pwd)
                        if uid is None:
                            st.error(f"Roll No. **{r_roll.strip()}** is already registered.")
                        else:
                            save_face_encodings_bulk(uid, st.session_state.reg_encodings)
                            if st.session_state.reg_profile:
                                save_profile_photo(uid, st.session_state.reg_profile)
                            if st.session_state.reg_photos:
                                save_dataset_photos(uid, r_roll.strip(), r_name.strip(), st.session_state.reg_photos)
                            st.session_state.reg_encodings = []
                            st.session_state.reg_photos = []
                            st.session_state.reg_profile = None
                            st.success(f"Account created! Log in with Roll No. **{r_roll.strip()}**.")

            with tab_tea:
                t_name  = st.text_input("Full Name *", placeholder="e.g. Dr. Anjali Mehta", key="t_name")
                t_id    = st.text_input("Teacher ID *", placeholder="e.g. T2024001", key="t_id")
                t_email = st.text_input("Email (optional)", placeholder="teacher@university.ac.in", key="t_email")
                t_dept  = st.text_input("Department *", placeholder="e.g. Computer Science", key="t_dept")
                t_pwd   = st.text_input("Choose Password *", type="password", key="t_pwd")
                t_pwd2  = st.text_input("Confirm Password *", type="password", key="t_pwd2")
                st.caption("Your account will be reviewed by the admin before you can log in.")

                if st.button("Submit Registration", use_container_width=True, type="primary", key="t_reg_btn"):
                    if not t_name.strip():
                        st.error("Full name is required.")
                    elif not t_id.strip():
                        st.error("Teacher ID is required.")
                    elif not t_dept.strip():
                        st.error("Department is required.")
                    elif not t_pwd:
                        st.error("Please choose a password.")
                    elif t_pwd != t_pwd2:
                        st.error("Passwords do not match.")
                    else:
                        result = create_teacher(name=t_name.strip(), teacher_id=t_id.strip(),
                                                email=t_email.strip(), department=t_dept.strip(),
                                                password=t_pwd)
                        if result is None:
                            st.error(f"Teacher ID **{t_id.strip()}** is already registered.")
                        else:
                            st.success("Registration submitted! You can log in once the admin approves your account.")

            st.divider()
            c1, c2 = st.columns([3, 2])
            with c1:
                st.markdown('<span class="switch-hint">Already have an account?</span>', unsafe_allow_html=True)
            with c2:
                if st.button("← Log In", use_container_width=True, key="go_login"):
                    st.session_state.auth_mode = "login"
                    st.rerun()

    st.markdown(
        "<div class='auth-footer'>University Face Recognition Attendance System</div>",
        unsafe_allow_html=True,
    )
    st.stop()

# ── Page content functions ─────────────────────────────────────────────────────
def teacher_dashboard():
    st.title("🎓 University Student Attendance System")
    st.caption("Face Recognition  •  " + date.today().strftime("%A, %B %d %Y"))

    today_records = get_today_attendance()
    all_students = get_all_users()
    encodings = load_all_face_encodings_db()

    col1, col2, col3, col4 = st.columns(4)
    present_unique = len({r["employee_id"] for r in today_records})
    col1.metric("Enrolled Students", len(all_students))
    col2.metric("Faces Trained", len(encodings))
    col3.metric("Present Today", present_unique)
    col4.metric("Absent Today", max(0, len(all_students) - present_unique))

    st.divider()
    st.subheader(f"Today's Attendance — {date.today().strftime('%B %d, %Y')}")

    if today_records:
        df = pd.DataFrame(today_records)
        df["check_in_time"] = pd.to_datetime(df["check_in_time"], errors="coerce").dt.strftime("%H:%M:%S")
        df["check_out_time"] = (
            pd.to_datetime(df["check_out_time"], errors="coerce")
            .dt.strftime("%H:%M:%S")
            .fillna("—")
        )
        df = df.rename(columns={
            "name": "Student Name",
            "employee_id": "Roll No.",
            "department": "Course",
            "check_in_time": "Check In",
            "check_out_time": "Check Out",
            "location": "Lecture Hall / Lab",
        })
        st.dataframe(
            df[["Student Name", "Roll No.", "Course", "Check In", "Check Out", "Lecture Hall / Lab"]],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No attendance recorded yet today.")


def student_dashboard():
    info = st.session_state.student_info
    st.title(f"Welcome, {info['name']}")
    st.caption(f"Roll No: {info['employee_id']}  •  {date.today().strftime('%A, %B %d %Y')}")

    col1, col2, col3 = st.columns(3)
    col1.metric("Course / Dept.", info.get("department") or "—")
    col2.metric("Semester", info.get("semester") or "—")
    col3.metric("Year", info.get("year") or "—")

    st.divider()
    st.subheader("My Attendance Records")

    records = get_student_attendance(info["id"])
    if records:
        df = pd.DataFrame(records)
        df["check_in_time"] = pd.to_datetime(df["check_in_time"], errors="coerce").dt.strftime("%H:%M:%S")
        df["check_out_time"] = (
            pd.to_datetime(df["check_out_time"], errors="coerce")
            .dt.strftime("%H:%M:%S")
            .fillna("—")
        )
        df = df.rename(columns={
            "date": "Date",
            "check_in_time": "Check In",
            "check_out_time": "Check Out",
            "location": "Lecture Hall / Lab",
            "status": "Status",
        })
        col_a, col_b = st.columns(2)
        col_a.metric("Total Days Present", df["Date"].nunique())
        col_b.metric("Last Check-In", df["Check In"].iloc[0] if not df.empty else "—")
        st.dataframe(
            df[["Date", "Check In", "Check Out", "Lecture Hall / Lab", "Status"]],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No attendance records found for your account.")


# ── Navigation (role-based) ────────────────────────────────────────────────────
if st.session_state.role in ("admin", "teacher"):
    pages = [
        st.Page(teacher_dashboard, title="Dashboard", icon="🎓", default=True),
        st.Page("pages/1_Register_Face.py", title="Register Face", icon="📸"),
        st.Page("pages/2_Mark_Attendance.py", title="Mark Attendance", icon="✅"),
        st.Page("pages/3_Manage_Users.py", title="Manage Users", icon="👥"),
        st.Page("pages/4_Reports.py", title="Reports", icon="📊"),
        st.Page("pages/5_Data_Viewer.py", title="Data Viewer", icon="🗄️"),
        st.Page("pages/6_Settings.py", title="Settings", icon="⚙️"),
    ]
else:
    pages = [
        st.Page(student_dashboard, title="My Attendance", icon="🎓", default=True),
        st.Page("pages/2_Mark_Attendance.py", title="Mark Attendance", icon="✅"),
        st.Page("pages/4_Reports.py", title="Reports", icon="📊"),
    ]

with st.sidebar:
    st.markdown("---")
    if st.button("Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.role = None
        st.session_state.student_info = None
        st.session_state.teacher_info = None
        st.rerun()

pg = st.navigation(pages)
pg.run()
