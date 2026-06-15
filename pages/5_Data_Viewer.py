import os
import streamlit as st
import pandas as pd
from PIL import Image

from utils.db_utils import init_db, get_connection, get_profile_photo, DATASET_DIR

init_db()


st.title("🗄️ Data Viewer")
st.caption("Browse all stored data — students, attendance records, and dataset photos")

tab_students, tab_attendance, tab_dataset = st.tabs(["Students", "Attendance Records", "Dataset Photos"])

# ── Students ───────────────────────────────────────────────────────────────────
with tab_students:
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT id, name, employee_id, department, semester, year, created_at, is_active FROM users ORDER BY created_at DESC",
        conn,
    )
    conn.close()

    total = len(df)
    active = int(df["is_active"].sum())
    has_photo = sum(1 for uid in df["id"] if get_profile_photo(uid))

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Registered", total)
    m2.metric("Active", active)
    m3.metric("With Profile Photo", has_photo)

    st.divider()

    show_inactive = st.toggle("Show deleted/inactive students", value=False)
    display_df = df if show_inactive else df[df["is_active"] == 1]

    for _, row in display_df.iterrows():
        col_photo, col_info = st.columns([1, 5])
        with col_photo:
            photo = get_profile_photo(int(row["id"]))
            if photo:
                st.image(photo, width=80)
            else:
                st.markdown("👤")
        with col_info:
            status = "✅ Active" if row["is_active"] else "❌ Deleted"
            st.markdown(
                f"**{row['name']}** &nbsp; `{row['employee_id']}` &nbsp; {status}  \n"
                f"{row['department']} · {row['semester']} · {row['year']}  \n"
                f"Registered: {row['created_at']}"
            )
        st.divider()

    csv = display_df.drop(columns=["id"]).to_csv(index=False)
    st.download_button("⬇ Download Students CSV", data=csv, file_name="students.csv", mime="text/csv")

# ── Attendance Records ─────────────────────────────────────────────────────────
with tab_attendance:
    conn = get_connection()
    df_att = pd.read_sql_query(
        """
        SELECT a.id, u.name, u.employee_id, u.department,
               a.date, a.check_in_time, a.check_out_time, a.location, a.status
        FROM attendance a
        JOIN users u ON a.user_id = u.id
        ORDER BY a.date DESC, a.check_in_time DESC
        """,
        conn,
    )
    conn.close()

    if df_att.empty:
        st.info("No attendance records yet.")
    else:
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Records", len(df_att))
        m2.metric("Unique Students", df_att["name"].nunique())
        m3.metric("Days Recorded", df_att["date"].nunique())

        # Filters
        fc1, fc2 = st.columns(2)
        with fc1:
            all_students = ["All"] + sorted(df_att["name"].unique().tolist())
            sel_student = st.selectbox("Filter by Student", all_students)
        with fc2:
            all_dates = ["All"] + sorted(df_att["date"].unique().tolist(), reverse=True)
            sel_date = st.selectbox("Filter by Date", all_dates)

        filtered = df_att.copy()
        if sel_student != "All":
            filtered = filtered[filtered["name"] == sel_student].copy()
        if sel_date != "All":
            filtered = filtered[filtered["date"] == sel_date].copy()

        filtered["check_in_time"] = pd.to_datetime(filtered["check_in_time"], errors="coerce").dt.strftime("%H:%M:%S")
        filtered["check_out_time"] = pd.to_datetime(filtered["check_out_time"], errors="coerce").dt.strftime("%H:%M:%S").fillna("—")

        display = filtered[["date", "name", "employee_id", "department", "check_in_time", "check_out_time", "location", "status"]].rename(
            columns={
                "date": "Date", "name": "Student", "employee_id": "Roll No.",
                "department": "Course", "check_in_time": "Check In",
                "check_out_time": "Check Out", "location": "Location", "status": "Status",
            }
        )

        st.dataframe(display, use_container_width=True, hide_index=True)

        csv = display.to_csv(index=False)
        st.download_button("⬇ Download CSV", data=csv, file_name="attendance_all.csv", mime="text/csv")

# ── Dataset Photos ─────────────────────────────────────────────────────────────
with tab_dataset:
    if not os.path.exists(DATASET_DIR) or not os.listdir(DATASET_DIR):
        st.info("No dataset photos yet. Register students to populate the dataset.")
    else:
        folders = sorted(os.listdir(DATASET_DIR))
        total_photos = sum(
            len([f for f in os.listdir(os.path.join(DATASET_DIR, folder)) if f.endswith(".jpg")])
            for folder in folders
        )

        m1, m2 = st.columns(2)
        m1.metric("Students in Dataset", len(folders))
        m2.metric("Total Photos", total_photos)

        st.divider()

        for folder in folders:
            folder_path = os.path.join(DATASET_DIR, folder)
            photos = sorted([f for f in os.listdir(folder_path) if f.endswith(".jpg")])
            with st.expander(f"📁 {folder}  ({len(photos)} photo{'s' if len(photos) != 1 else ''})", expanded=True):
                if photos:
                    cols = st.columns(min(len(photos), 5))
                    for i, photo_file in enumerate(photos):
                        with cols[i % 5]:
                            img = Image.open(os.path.join(folder_path, photo_file))
                            st.image(img, caption=photo_file, use_container_width=True)
                else:
                    st.caption("No photos in this folder.")
