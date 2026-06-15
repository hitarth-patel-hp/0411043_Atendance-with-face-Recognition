import calendar
import streamlit as st
import pandas as pd
from datetime import date, timedelta

from utils.db_utils import init_db, get_attendance_by_date_range, get_attendance_summary, get_all_users

try:
    import plotly.express as px
    _HAS_PLOTLY = True
except ImportError:
    _HAS_PLOTLY = False

init_db()


is_teacher = st.session_state.get("role") == "admin"
student_info = st.session_state.get("student_info")

# ══════════════════════════════════════════════════════════════════════════════
# STUDENT — MY REPORTS VIEW
# ══════════════════════════════════════════════════════════════════════════════
if not is_teacher:
    st.title("📊 My Attendance Report")

    tab_range, tab_monthly = st.tabs(["Date Range", "Monthly Summary"])

    with tab_range:
        c1, c2 = st.columns(2)
        with c1:
            start = st.date_input("From", date.today() - timedelta(days=30))
        with c2:
            end = st.date_input("To", date.today())

        if start > end:
            st.error("'From' date must be before 'To' date.")
        else:
            records = get_attendance_by_date_range(start.isoformat(), end.isoformat(), student_info["id"])
            if not records:
                st.info("No records found for the selected date range.")
            else:
                df = pd.DataFrame(records)
                df["check_in_time"] = pd.to_datetime(df["check_in_time"], errors="coerce").dt.strftime("%H:%M:%S")
                df["check_out_time"] = (
                    pd.to_datetime(df["check_out_time"], errors="coerce")
                    .dt.strftime("%H:%M:%S")
                    .fillna("—")
                )
                display = df[["date", "check_in_time", "check_out_time", "location"]].rename(
                    columns={
                        "date": "Date",
                        "check_in_time": "Check In",
                        "check_out_time": "Check Out",
                        "location": "Lecture Hall / Lab",
                    }
                )
                m1, m2 = st.columns(2)
                m1.metric("Total Sessions", len(display))
                m2.metric("Days Present", df["date"].nunique())

                st.dataframe(display, use_container_width=True, hide_index=True)
                st.download_button(
                    "⬇ Download CSV",
                    data=display.to_csv(index=False),
                    file_name=f"my_attendance_{start}_{end}.csv",
                    mime="text/csv",
                )

                if _HAS_PLOTLY and len(df) > 1:
                    daily = df.groupby("date").size().reset_index(name="Sessions")
                    fig = px.bar(daily, x="date", y="Sessions", title="My Daily Sessions")
                    fig.update_layout(xaxis_tickangle=-30)
                    st.plotly_chart(fig, use_container_width=True)

    with tab_monthly:
        c1, c2 = st.columns(2)
        with c1:
            sel_year = st.number_input("Year", min_value=2020, max_value=2035, value=date.today().year, step=1)
        with c2:
            month_names = [date(2000, m, 1).strftime("%B") for m in range(1, 13)]
            sel_month_name = st.selectbox("Month", month_names, index=date.today().month - 1)
            sel_month = month_names.index(sel_month_name) + 1

        _, days_in_month = calendar.monthrange(int(sel_year), sel_month)
        month_start = date(int(sel_year), sel_month, 1).isoformat()
        month_end = date(int(sel_year), sel_month, days_in_month).isoformat()
        month_records = get_attendance_by_date_range(month_start, month_end, student_info["id"])

        days_present = len({r["date"] for r in month_records})
        pct = round(days_present / days_in_month * 100, 1) if days_in_month else 0

        m1, m2, m3 = st.columns(3)
        m1.metric("Days Present", days_present)
        m2.metric("Working Days", days_in_month)
        m3.metric("Attendance %", f"{pct}%")

        if pct < 75:
            st.warning(f"Your attendance is below 75% for {sel_month_name} {sel_year}.")
        elif month_records:
            st.success(f"Good attendance for {sel_month_name} {sel_year}!")
        else:
            st.info(f"No records for {sel_month_name} {sel_year}.")

    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# TEACHER FULL REPORTS VIEW
# ══════════════════════════════════════════════════════════════════════════════
st.title("📊 Attendance Reports")

tab_range, tab_monthly = st.tabs(["Date Range Report", "Monthly Summary"])

# ── Date range report ──────────────────────────────────────────────────────────
with tab_range:
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        start = st.date_input("From", date.today() - timedelta(days=7))
    with c2:
        end = st.date_input("To", date.today())
    with c3:
        students = get_all_users()
        opts = {"All Students": None}
        opts.update({f"{s['name']} ({s['employee_id']})": s["id"] for s in students})
        selected = st.selectbox("Filter by Student", list(opts.keys()))

    if start > end:
        st.error("'From' date must be before 'To' date.")
    else:
        records = get_attendance_by_date_range(start.isoformat(), end.isoformat(), opts[selected])

        if not records:
            st.info("No records found for the selected filters.")
        else:
            df = pd.DataFrame(records)
            df["check_in_time"] = pd.to_datetime(df["check_in_time"], errors="coerce").dt.strftime("%H:%M:%S")
            df["check_out_time"] = (
                pd.to_datetime(df["check_out_time"], errors="coerce")
                .dt.strftime("%H:%M:%S")
                .fillna("—")
            )

            display = df[["date", "name", "employee_id", "department", "check_in_time", "check_out_time", "location"]].rename(
                columns={
                    "date": "Date",
                    "name": "Student Name",
                    "employee_id": "Roll No.",
                    "department": "Course",
                    "check_in_time": "Check In",
                    "check_out_time": "Check Out",
                    "location": "Lecture Hall / Lab",
                }
            )

            m1, m2, m3 = st.columns(3)
            m1.metric("Total Records", len(display))
            m2.metric("Unique Students", df["name"].nunique())
            m3.metric("Date Range", f"{start} → {end}")

            st.dataframe(display, use_container_width=True, hide_index=True)

            csv = display.to_csv(index=False)
            st.download_button(
                "⬇ Download CSV",
                data=csv,
                file_name=f"attendance_{start}_{end}.csv",
                mime="text/csv",
            )

            if _HAS_PLOTLY and len(df) > 1:
                daily = df.groupby("date").size().reset_index(name="Present")
                fig = px.bar(
                    daily, x="date", y="Present",
                    title="Daily Attendance Count",
                    labels={"date": "Date"},
                )
                fig.update_layout(xaxis_tickangle=-30)
                st.plotly_chart(fig, use_container_width=True)

# ── Monthly summary ────────────────────────────────────────────────────────────
with tab_monthly:
    c1, c2 = st.columns(2)
    with c1:
        sel_year = st.number_input("Year", min_value=2020, max_value=2035, value=date.today().year, step=1)
    with c2:
        month_names = [date(2000, m, 1).strftime("%B") for m in range(1, 13)]
        sel_month_name = st.selectbox("Month", month_names, index=date.today().month - 1)
        sel_month = month_names.index(sel_month_name) + 1

    summary = get_attendance_summary(int(sel_year), sel_month)

    if not summary:
        st.info("No data available for the selected month.")
    else:
        _, days_in_month = calendar.monthrange(int(sel_year), sel_month)
        df_s = pd.DataFrame(summary)
        df_s["Attendance %"] = (df_s["days_present"] / days_in_month * 100).round(1)
        df_s = df_s.rename(columns={
            "name": "Student Name",
            "department": "Course",
            "days_present": "Days Present",
        })

        m1, m2, m3 = st.columns(3)
        m1.metric("Total Students", len(df_s))
        m2.metric("Working Days", days_in_month)
        avg = round(df_s["Days Present"].mean(), 1) if len(df_s) else 0
        m3.metric("Avg Days Present", avg)

        def highlight_low(row):
            color = "background-color: #ffeeba" if row["Attendance %"] < 75 else ""
            return [color] * len(row)

        styled = df_s[["Student Name", "Course", "Days Present", "Attendance %"]].style.apply(
            highlight_low, axis=1
        )
        st.dataframe(styled, use_container_width=True, hide_index=True)
        st.caption("⚠️ Yellow = below 75% attendance threshold")

        csv = df_s.to_csv(index=False)
        st.download_button(
            "⬇ Download CSV",
            data=csv,
            file_name=f"monthly_{sel_year}_{sel_month:02d}.csv",
            mime="text/csv",
        )

        if _HAS_PLOTLY:
            fig = px.bar(
                df_s, x="Student Name", y="Days Present",
                color="Attendance %",
                color_continuous_scale="RdYlGn",
                range_color=[0, 100],
                title=f"Monthly Attendance — {sel_month_name} {sel_year}",
            )
            fig.add_hline(
                y=days_in_month * 0.75,
                line_dash="dash", line_color="red",
                annotation_text="75% threshold",
            )
            fig.update_layout(xaxis_tickangle=-30)
            st.plotly_chart(fig, use_container_width=True)
