import streamlit as st
from datetime import date, datetime
from PIL import Image

from utils.db_utils import (
    init_db, get_all_users, mark_checkin,
    get_today_attendance, get_user_by_id,
)
from utils.face_utils import recognize_faces, draw_annotations, load_encodings

init_db()


is_teacher = st.session_state.get("role") == "admin"
student_info = st.session_state.get("student_info")

# ══════════════════════════════════════════════════════════════════════════════
# STUDENT SELF CHECK-IN VIEW
# ══════════════════════════════════════════════════════════════════════════════
if not is_teacher:
    st.title("✅ My Check-In / Check-Out")
    st.write(f"**{date.today().strftime('%A, %B %d, %Y')}**")
    st.info(f"Checking in as: **{student_info['name']}** — Roll No. `{student_info['employee_id']}`")

    encodings = load_encodings()
    if not encodings:
        st.warning("No face data found. Please ask your teacher to register your face first.")
        st.stop()

    c1, c2 = st.columns([2, 2])
    with c1:
        lecture_hall = st.text_input("Lecture Hall / Lab", value="Lecture Hall 101")
    with c2:
        subject = st.text_input("Subject", placeholder="Data Structures")

    location_label = lecture_hall.strip() + (f" | {subject.strip()}" if subject.strip() else "")

    camera_img = st.camera_input("Take a photo to verify your face")

    if camera_img:
        if st.button("Submit", type="primary", use_container_width=True):
            if not subject.strip():
                st.error("Please enter a subject name before submitting.")
                st.stop()
            img = Image.open(camera_img)
            with st.spinner("Verifying your face…"):
                results, error = recognize_faces(img)

            if error:
                st.error(error)
            elif not results:
                st.warning("No face detected. Please ensure you are clearly visible and well-lit.")
            else:
                matched = [r for r in results if r["user_id"] == student_info["id"]]
                if not matched:
                    st.error("Your face was not recognized. Please try again or contact your teacher.")
                else:
                    status, _ = mark_checkin(student_info["id"], location_label)
                    if status == "success":
                        st.success(f"Check-in recorded for **{location_label}**!")
                    elif status == "already_in":
                        st.info(f"You are already checked in for **{location_label}** today.")
                    else:
                        st.warning(f"Your session for **{location_label}** is already complete.")

    st.divider()
    st.subheader("My Attendance Today")
    if st.button("Refresh", use_container_width=True):
        st.rerun()
    today_all = get_today_attendance()
    my_records = [r for r in today_all if r["user_id"] == student_info["id"]]
    if my_records:
        for r in my_records:
            ci = r.get("check_in_time") or ""
            co = r.get("check_out_time") or ""
            try:
                ci = datetime.fromisoformat(ci).strftime("%H:%M") if ci else "—"
            except ValueError:
                ci = "—"
            try:
                co = datetime.fromisoformat(co).strftime("%H:%M") if co else "—"
            except ValueError:
                co = "—"
            st.write(f"**{r['location']}**  |  In: {ci}  |  Out: {co}")
    else:
        st.info("No attendance recorded for you today yet.")
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# TEACHER FULL VIEW
# ══════════════════════════════════════════════════════════════════════════════
st.title("✅ Mark Attendance")
st.write(f"**{date.today().strftime('%A, %B %d, %Y')}**")

encodings = load_encodings()
if not encodings:
    st.warning("No student faces trained yet. Please register students first on the **Register Student** page.")
    st.stop()

# Classroom selector — drives both capture and the status panel
c1, c2 = st.columns([2, 2])
with c1:
    lecture_hall = st.text_input("Lecture Hall / Lab", value="Lecture Hall 101")
with c2:
    subject = st.text_input("Subject", placeholder="Data Structures")

location_label = lecture_hall.strip() + (f" | {subject.strip()}" if subject.strip() else "")

st.divider()

# Fetch once, shared across both columns
all_students = get_all_users()
today_all = get_today_attendance()

col_cam, col_status = st.columns([1, 1], gap="large")

# ── Camera panel ───────────────────────────────────────────────────────────────
with col_cam:
    st.subheader("Capture")

    camera_img = st.camera_input("Take attendance photo — multiple students can be in frame")

    if camera_img:
        if st.button("Process Attendance", type="primary", use_container_width=True):
            if not subject.strip():
                st.error("Please enter a subject name before processing attendance.")
                st.stop()
            img = Image.open(camera_img)
            user_map = {u["id"]: u["name"] for u in all_students}

            with st.spinner("Scanning faces…"):
                results, error = recognize_faces(img)

            if error:
                st.error(error)
            elif not results:
                st.warning("No faces detected. Ensure students are clearly visible and well-lit.")
            else:
                annotated = draw_annotations(img, results, user_map)
                st.image(annotated, caption=f"Detected {len(results)} face(s)", use_container_width=True)

                st.markdown("**Results:**")
                for r in results:
                    uid = r["user_id"]
                    conf = r["confidence"]

                    if uid is None:
                        st.error("❌ Unrecognized student")
                        continue

                    student = get_user_by_id(uid)
                    sname = student["name"] if student else f"ID:{uid}"
                    roll  = student.get("employee_id", "") if student else ""

                    status, _ = mark_checkin(uid, location_label)
                    if status == "success":
                        st.success(f"✅ **{sname}** `{roll}` — Present  •  {conf}% match")
                    elif status == "already_in":
                        st.info(f"ℹ️ **{sname}** `{roll}` — Already marked present for **{location_label}**")
                    else:
                        st.warning(f"⚠️ **{sname}** `{roll}` — Session already complete for **{location_label}**")

# ── Today's status — one record per student per day ───────────────────────────
with col_status:
    st.subheader("Today's Status")

    if st.button("Refresh", use_container_width=True):
        st.rerun()

    present_ids = {r["employee_id"] for r in today_all}

    present_tab, absent_tab = st.tabs([
        f"Present ({len(present_ids)})",
        f"Absent ({len(all_students) - len(present_ids)})",
    ])

    with present_tab:
        if not today_all:
            st.info("No one marked present yet today.")
        seen = set()
        for r in today_all:
            if r["employee_id"] in seen:
                continue
            seen.add(r["employee_id"])
            ci = r.get("check_in_time") or ""
            co = r.get("check_out_time") or ""
            try:
                ci = datetime.fromisoformat(ci).strftime("%H:%M") if ci else "—"
            except ValueError:
                ci = "—"
            try:
                co = datetime.fromisoformat(co).strftime("%H:%M") if co else "—"
            except ValueError:
                co = "—"
            st.write(f"**{r['name']}** `{r['employee_id']}`")
            st.caption(f"In: {ci}  |  Out: {co}  |  {r.get('location', '')}")
            st.divider()

    with absent_tab:
        absent = [s for s in all_students if s["employee_id"] not in present_ids]
        if not absent:
            st.success("All enrolled students are present!")
        for s in absent:
            st.write(f"**{s['name']}** `{s['employee_id']}`")
            st.caption(s.get("department") or "—")
            st.divider()
