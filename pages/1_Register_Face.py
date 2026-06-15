import io
import streamlit as st
from PIL import Image

from utils.db_utils import init_db, create_user, get_all_users, load_all_face_encodings_db, save_profile_photo, get_profile_photo, save_dataset_photos
from utils.face_utils import encode_image, save_face_encodings_bulk

init_db()


st.title("📸 Register New Student")
st.caption("Camera-only enrollment — multiple photos improve recognition accuracy")

# ── Session state ──────────────────────────────────────────────────────────────
if "train_encodings" not in st.session_state:
    st.session_state.train_encodings = []
if "train_photos" not in st.session_state:
    st.session_state.train_photos = []  # all captured photo bytes for dataset
if "profile_photo_bytes" not in st.session_state:
    st.session_state.profile_photo_bytes = None  # first captured photo saved as profile

MIN_SAMPLES = 3
MAX_SAMPLES = 5

col_form, col_cam = st.columns([1, 1], gap="large")

# ── Student info form ──────────────────────────────────────────────────────────
with col_form:
    st.subheader("Student Details")

    name    = st.text_input("Full Name *", placeholder="Rahul Sharma")
    roll_no = st.text_input("Roll Number *", placeholder="22BCS045")
    course  = st.text_input("Course / Branch *", placeholder="B.Tech Computer Science")
    col_s, col_y = st.columns(2)
    with col_s:
        semester = st.selectbox("Semester", [f"Sem {i}" for i in range(1, 9)])
    with col_y:
        year = st.selectbox("Year", ["1st Year", "2nd Year", "3rd Year", "4th Year"])
    email = st.text_input("Email (optional)", placeholder="student@university.edu")

    st.divider()

    count = len(st.session_state.train_encodings)
    if count == 0:
        st.info(f"Capture at least **{MIN_SAMPLES} photos** using the camera on the right.")
    elif count < MIN_SAMPLES:
        st.warning(f"**{count}/{MIN_SAMPLES}** training photos captured. Need {MIN_SAMPLES - count} more.")
    else:
        st.success(f"**{count}/{MAX_SAMPLES}** training photos ready.")

    # Show profile photo preview
    if st.session_state.profile_photo_bytes:
        st.image(st.session_state.profile_photo_bytes, caption="Profile Photo (1st capture)", width=150)

    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        register_clicked = st.button(
            "Register Student",
            type="primary",
            use_container_width=True,
            disabled=(count < MIN_SAMPLES),
        )
    with btn_col2:
        if st.button("Clear Photos", use_container_width=True):
            st.session_state.train_encodings = []
            st.session_state.train_photos = []
            st.session_state.profile_photo_bytes = None
            st.rerun()

    if register_clicked:
        if not name.strip() or not roll_no.strip() or not course.strip():
            st.error("Name, Roll Number, and Course are required.")
        elif len(st.session_state.train_encodings) < MIN_SAMPLES:
            st.error(f"Please capture at least {MIN_SAMPLES} training photos.")
        else:
            uid = create_user(name.strip(), roll_no.strip(), email.strip(), course.strip(), semester, year)
            if uid is None:
                st.error(f"Roll number **{roll_no}** already exists.")
            else:
                ok = save_face_encodings_bulk(uid, st.session_state.train_encodings)
                # Save profile photo permanently
                if st.session_state.profile_photo_bytes:
                    save_profile_photo(uid, st.session_state.profile_photo_bytes)
                # Save all training photos to dataset folder
                if st.session_state.train_photos:
                    folder = save_dataset_photos(uid, roll_no.strip(), name.strip(), st.session_state.train_photos)
                    st.info(f"Photos saved to `{folder}`")
                if ok:
                    st.success(f"✅ **{name}** registered with {count} training photos!")
                    st.session_state.train_encodings = []
                    st.session_state.train_photos = []
                    st.session_state.profile_photo_bytes = None
                else:
                    st.error("Failed to save face data.")

# ── Camera capture panel ───────────────────────────────────────────────────────
with col_cam:
    st.subheader("Face Training Camera")

    count = len(st.session_state.train_encodings)
    st.progress(min(count / MAX_SAMPLES, 1.0), text=f"{count}/{MAX_SAMPLES} samples captured")

    camera_img = st.camera_input(
        "Position face clearly in frame, then click Add Sample",
        key="reg_camera",
    )

    if camera_img:
        img = Image.open(camera_img)
        if count < MAX_SAMPLES:
            if st.button("➕ Add Training Sample", type="primary", use_container_width=True):
                encoding, err = encode_image(img)
                if err:
                    st.error(err)
                else:
                    st.session_state.train_encodings.append(encoding)
                    # Save photo bytes for dataset + profile
                    buf = io.BytesIO()
                    img.convert("RGB").save(buf, format="JPEG", quality=85)
                    photo_bytes = buf.getvalue()
                    st.session_state.train_photos.append(photo_bytes)
                    if st.session_state.profile_photo_bytes is None:
                        st.session_state.profile_photo_bytes = photo_bytes
                    st.success(f"Sample {len(st.session_state.train_encodings)} captured!")
                    st.rerun()
        else:
            st.info(f"Max {MAX_SAMPLES} samples reached. Click **Register Student**.")

    st.divider()
    st.markdown("""
**Tips for better recognition:**
- Look directly at the camera
- Ensure your face is well-lit
- Slightly vary your angle across shots
- Remove glasses for one shot if possible
""")

# ── Enrolled students grid ─────────────────────────────────────────────────────
st.divider()
st.subheader("Enrolled Students")

students = get_all_users()
encodings = load_all_face_encodings_db()

if not students:
    st.info("No students enrolled yet.")
else:
    cols = st.columns(4)
    for i, s in enumerate(students):
        with cols[i % 4]:
            uid = s["id"]
            photo = get_profile_photo(uid)
            if photo:
                st.image(photo, use_container_width=True)
            else:
                st.markdown("👤")
            has_face = uid in encodings
            sample_count = len(encodings.get(uid, []))
            st.markdown(
                f"**{s['name']}**  \n`{s['employee_id']}`  \n"
                f"{s.get('department') or ''}  \n"
                + (f"✅ {sample_count} samples" if has_face else "⚠️ No face data")
            )
