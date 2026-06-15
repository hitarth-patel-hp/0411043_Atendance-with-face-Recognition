import io
import streamlit as st
from PIL import Image

from utils.db_utils import (
    init_db, get_all_users, delete_user,
    load_all_face_encodings_db,
    save_profile_photo, get_profile_photo,
    get_pending_teachers, approve_teacher, reject_teacher,
)
from utils.face_utils import (
    delete_face_encodings, encode_image,
    save_face_encodings_bulk, load_face_encodings_db,
)

init_db()

st.title("👥 Manage Users")

# ── Pending Teacher Approvals (super-admin only) ───────────────────────────────
if st.session_state.get("role") == "admin":
    pending = get_pending_teachers()
    if pending:
        st.warning(f"⏳ {len(pending)} pending teacher registration(s) awaiting your approval")
        with st.expander("👨‍🏫 Review Pending Teacher Registrations", expanded=True):
            for t in pending:
                c1, c2, c3 = st.columns([4, 1, 1])
                with c1:
                    st.markdown(
                        f"**{t['name']}** &nbsp;|&nbsp; ID: `{t['teacher_id']}` &nbsp;|&nbsp; "
                        f"{t.get('department') or '—'} &nbsp;|&nbsp; {t.get('email') or 'no email'} &nbsp;|&nbsp; "
                        f"Registered: {(t.get('created_at') or '')[:10]}"
                    )
                with c2:
                    if st.button("✅ Approve", key=f"approve_{t['id']}", use_container_width=True, type="primary"):
                        approve_teacher(t["id"])
                        st.success(f"{t['name']} approved!")
                        st.rerun()
                with c3:
                    if st.button("❌ Reject", key=f"reject_{t['id']}", use_container_width=True):
                        reject_teacher(t["id"])
                        st.error(f"{t['name']} rejected.")
                        st.rerun()
        st.divider()

st.subheader("Students")

students = get_all_users()
encodings = load_all_face_encodings_db()

if not students:
    st.info("No students enrolled yet.")
    st.stop()

c1, c2, c3 = st.columns(3)
c1.metric("Total Students", len(students))
c2.metric("Faces Trained", sum(1 for s in students if s["id"] in encodings))
c3.metric("Missing Face Data", sum(1 for s in students if s["id"] not in encodings))

st.divider()

search = st.text_input("Search by name, roll number, or course", "")
filtered = [
    s for s in students
    if not search
    or search.lower() in s["name"].lower()
    or search.lower() in (s.get("employee_id") or "").lower()
    or search.lower() in (s.get("department") or "").lower()
]

for s in filtered:
    uid = s["id"]
    has_face = uid in encodings
    sample_count = len(encodings.get(uid, []))
    badge = f"✅ {sample_count} sample(s)" if has_face else "⚠️ Not trained"

    # Session state keys
    retrain_key  = f"show_retrain_{uid}"
    samples_key  = f"retrain_samples_{uid}"
    if retrain_key not in st.session_state:
        st.session_state[retrain_key] = False
    if samples_key not in st.session_state:
        st.session_state[samples_key] = []

    with st.expander(f"{'✅' if has_face else '⚠️'}  {s['name']}  —  {s['employee_id']}"):
        c_photo, c_info, c_actions = st.columns([1, 2, 1])

        # ── Profile photo ──────────────────────────────────────────────────────
        with c_photo:
            photo = get_profile_photo(uid)
            if photo:
                st.image(photo, caption="Profile Photo", use_container_width=True)
            else:
                st.markdown(
                    "<div style='width:100%;height:140px;background:#f0f2f6;"
                    "border-radius:8px;display:flex;align-items:center;"
                    "justify-content:center;font-size:48px'>👤</div>",
                    unsafe_allow_html=True,
                )
                st.caption("No photo saved")

        # ── Student info ───────────────────────────────────────────────────────
        with c_info:
            st.markdown(f"**Name:** {s['name']}")
            st.markdown(f"**Roll Number:** `{s['employee_id']}`")
            st.markdown(f"**Course:** {s.get('department') or '—'}")
            st.markdown(f"**Semester:** {s.get('semester') or '—'}")
            st.markdown(f"**Year:** {s.get('year') or '—'}")
            st.markdown(f"**Email:** {s.get('email') or '—'}")
            created = (s.get("created_at") or "")[:10]
            st.markdown(f"**Enrolled On:** {created or '—'}")
            st.markdown(f"**Face Status:** {badge}")

            # Toggle retrain section
            btn_label = "🔄 Cancel Retrain" if st.session_state[retrain_key] else "📷 Retrain Face"
            if st.button(btn_label, key=f"toggle_{uid}"):
                st.session_state[retrain_key] = not st.session_state[retrain_key]
                st.session_state[samples_key] = []
                st.rerun()

        # ── Actions ────────────────────────────────────────────────────────────
        with c_actions:
            st.markdown("&nbsp;")
            if has_face:
                if st.button("Remove Face Data", key=f"rf_{uid}", use_container_width=True):
                    delete_face_encodings(uid)
                    st.warning("Face data removed.")
                    st.rerun()
            st.markdown("&nbsp;")
            if st.button("Delete Student", key=f"del_{uid}", type="secondary", use_container_width=True):
                delete_user(uid)
                delete_face_encodings(uid)
                st.error(f"{s['name']} removed.")
                st.rerun()

        # ── Retrain section (only shown when toggled on) ───────────────────────
        if st.session_state[retrain_key]:
            st.divider()
            pending = len(st.session_state[samples_key])
            st.info(f"Retrain mode — {pending} new sample(s) captured so far. Capture at least 3.")

            cam = st.camera_input("Take a new training photo", key=f"cam_{uid}")
            if cam:
                img = Image.open(cam)
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    if st.button("➕ Add Sample", key=f"add_{uid}", type="primary"):
                        enc, err = encode_image(img)
                        if err:
                            st.error(err)
                        else:
                            st.session_state[samples_key].append(enc)
                            # Update profile photo with latest capture
                            buf = io.BytesIO()
                            img.convert("RGB").save(buf, format="JPEG", quality=85)
                            save_profile_photo(uid, buf.getvalue())
                            st.success(f"Sample {len(st.session_state[samples_key])} added + photo updated!")
                            st.rerun()
                with col_b:
                    if pending >= 1 and st.button("💾 Save Face Data", key=f"save_{uid}", type="primary"):
                        existing = load_face_encodings_db(uid)
                        merged = existing + st.session_state[samples_key]
                        save_face_encodings_bulk(uid, merged)
                        st.session_state[samples_key] = []
                        st.session_state[retrain_key] = False
                        st.success("✅ Face data saved permanently to database!")
                        st.rerun()
                with col_c:
                    if st.button("Clear New Samples", key=f"clr_{uid}"):
                        st.session_state[samples_key] = []
                        st.rerun()
