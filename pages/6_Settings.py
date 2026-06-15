import streamlit as st
from utils.db_utils import init_db

init_db()


st.title("⚙️ Settings")

st.info("Location restriction has been removed. Attendance can be marked from any device without GPS verification.")

st.divider()
st.markdown("""
**How multi-classroom attendance works:**

- On the **Mark Attendance** page, set the **Lecture Hall / Lab** and optionally the **Subject**.
- Each unique classroom name is tracked as a separate session — the same student can be marked present in multiple classrooms on the same day.
- The Present / Absent panel on that page shows attendance **for the currently selected classroom only**.
- All records (across all classrooms) are visible in **Data Viewer → Attendance Records** and in **Reports**.
""")
