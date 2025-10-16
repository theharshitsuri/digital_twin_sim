import streamlit as st
import pandas as pd
import json
import plotly.express as px

# --- Page Config ---
st.set_page_config(page_title="Digital Twin Simulation", layout="wide")
st.title("Interactive Student Progression Dashboard")

# --- Load Synthetic Students Data ---
try:
    with open("data/synthetic_students.json", "r") as file:
        students_data = json.load(file)
    students_df = pd.DataFrame(students_data)
except FileNotFoundError:
    st.error("No synthetic_students.json found. Please ensure the file is available.")
    st.stop()

# --- Load Student Outcomes Data ---
try:
    student_outcomes = pd.read_csv("data/student_outcomes.csv")
except FileNotFoundError:
    st.error("No student_outcomes.csv found. Please ensure the file is available.")
    st.stop()

# --- Normalize Column Names for Consistency ---
students_df.columns = students_df.columns.str.lower()  # Normalize column names to lowercase
student_outcomes.columns = student_outcomes.columns.str.lower()  # Normalize column names to lowercase

# --- Merge DataFrames on ID ---
merged_df = pd.merge(students_df, student_outcomes, on="id", how="inner")  # Merge using 'id' column

# --- Filter by Admission Term ---
admission_terms = merged_df['admission_term_y'].unique()  # Get unique admission terms
selected_term = st.selectbox("Select Admission Term", admission_terms)

filtered_df = merged_df[merged_df['admission_term_y'] == selected_term]

# --- Filter by Graduation Status ---
status_options = ['Graduated', 'Dropped Out', 'Enrolled']
selected_status = st.multiselect("Select Graduation Status", status_options, default=status_options)

# Apply filters based on selected status
if 'Graduated' in selected_status:
    filtered_df = filtered_df[filtered_df['graduated_y'] == True]
if 'Dropped Out' in selected_status:
    filtered_df = filtered_df[filtered_df['dropped_out_y'] == True]
if 'Enrolled' in selected_status:
    filtered_df = filtered_df[
        (filtered_df['graduated_y'] == False) & 
        (filtered_df['dropped_out_y'] == False)
    ]

# --- Check if filtered_df has data ---
if filtered_df.empty:
    st.warning("No students match the selected filters.")
else:
    # --- Create Timeline for Student Progression ---
    timeline_data = []

    # Loop through the filtered students and their progression
    for _, student in filtered_df.iterrows():
        for semester in range(1, 13):  # Loop through semesters 1 to 12
            courses = student['study_plan'].get(str(semester), [])
            
            # Determine the student's status for this semester
            if student['graduated_y']:
                status = 'Graduated'
            elif student['dropped_out_y']:
                status = 'Dropped Out'
            elif courses:  # If courses exist, the student is enrolled
                status = 'Enrolled'
            else:
                status = 'Not Enrolled'
            
            # Add student id to the timeline data (use 'id' here)
            timeline_data.append({
                "student_id": student['id'],  # Ensure student_id is added
                "semester": semester,
                "status": status,
                "start_date": f"2025-01-01",  # Dummy start date for visualizing timeline
                "end_date": f"2025-01-{semester+1}",  # Dummy end date
            })

    # Convert timeline data to DataFrame
    timeline_df = pd.DataFrame(timeline_data)

    # --- Plot Gantt Chart ---
    if len(timeline_df) > 0:  # Only plot if timeline_df has data
        fig = px.timeline(timeline_df, x_start="start_date", x_end="end_date", y="student_id", color="status", title="Student Progression Over Time")
        fig.update_yaxes(categoryorder="total ascending")  # To keep students in order
        fig.update_layout(showlegend=True)

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data available to plot the timeline.")

    # --- Download Button ---
    st.subheader("Export Filtered Data")
    st.download_button(
        label="Download Filtered Results",
        data=filtered_df.to_csv(index=False).encode("utf-8"),
        file_name="filtered_student_progress.csv",
        mime="text/csv",
    )
