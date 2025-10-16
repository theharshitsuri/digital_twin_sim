"""
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# --- Page Config ---
st.set_page_config(page_title="Digital Twin Simulation", layout="wide")
st.title("Digital Twin Simulation Dashboard")

# --- Load Simulation Results ---
try:
    results = pd.read_csv("data/results.csv")
except FileNotFoundError:
    st.error("No results.csv found. Run `python -m src.simulation_runner` first.")
    st.stop()

# --- Summary Stats ---
st.subheader("Final Snapshot")
final_row = results.tail(1).to_dict("records")[0]
col1, col2, col3 = st.columns(3)
col1.metric("Graduated", final_row["Graduated"])
col2.metric("Dropped Out", final_row["DroppedOut"])
col3.metric("Still Enrolled", final_row["Enrolled"])

# --- Show Table ---
st.subheader("Simulation Results by Semester")
st.dataframe(results)

# --- Plot Results ---
st.subheader("Graduation vs Dropout vs Enrollment")
fig, ax = plt.subplots(figsize=(8, 5))
results.set_index("Semester")[["Graduated", "DroppedOut", "Enrolled"]].plot(ax=ax, marker="o")
ax.set_xlabel("Semester")
ax.set_ylabel("Number of Students")
ax.set_title("Student Progression Over Time")
st.pyplot(fig)

# --- Extra Option: Download Results ---
st.subheader("Export Results")
st.download_button(
    label="Download results as CSV",
    data=results.to_csv(index=False).encode("utf-8"),
    file_name="simulation_results.csv",
    mime="text/csv",
)
"""
import streamlit as st
import pandas as pd
import json
import matplotlib.pyplot as plt
import seaborn as sns

# --- Page Config ---
st.set_page_config(page_title="Digital Twin Simulation", layout="wide")
st.title("Digital Twin Simulation Dashboard")

# --- Load Synthetic Students Data ---
try:
    with open("data/synthetic_students.json", "r") as file:
        students_data = json.load(file)
    # Convert to DataFrame for easier processing
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

# --- Check Column Names Before Merging ---
#st.write("Students DataFrame Columns:", students_df.columns)
#st.write("Student Outcomes DataFrame Columns:", student_outcomes.columns)

# --- Normalize Column Names to Match for Merge ---
# Convert columns in both DataFrames to lowercase for consistency
students_df.columns = students_df.columns.str.lower()  # Convert all column names to lowercase
student_outcomes.columns = student_outcomes.columns.str.lower()  # Convert all column names to lowercase

# --- Merge DataFrames on ID ---
merged_df = pd.merge(students_df, student_outcomes, on="id", how="inner")  # Merge using 'id' column

# --- Check Column Names After Merging ---
#st.write("Merged DataFrame Columns:", merged_df.columns)

# --- Summary Stats ---
#st.subheader("Final Snapshot")

# Get the last row for summary stats
final_row = merged_df.tail(1).to_dict("records")[0]

# Print final_row to check its contents
#st.write("Final Row:", final_row)

# --- Check for existence of 'graduated', 'dropped_out', and 'enrolled' in final_row ---
col1, col2, col3 = st.columns(3)

# Use '_y' suffix columns (from student_outcomes.csv)

# --- Show Table ---
st.subheader("Simulation Results by Semester")
st.dataframe(merged_df)



# --- Plot 1: Graduation Funnel by Admission Term ---
st.subheader("Graduation Funnel by Admission Term")

# Check the column names in merged_df to see the correct name for 'admission_term'
if 'admission_term_y' in merged_df.columns:
    status_counts = (
        merged_df.assign(status=merged_df.apply(
            lambda x: "Graduated" if x["graduated_y"] else ("Dropped" if x["dropped_out_y"] else "Enrolled"), axis=1))
        .groupby(["admission_term_y", "status"])
        .size()
        .reset_index(name="count")
    )
else:
    st.error("'admission_term_y' column not found in merged_df")

fig, ax = plt.subplots(figsize=(10, 6))  # Adjusted size for better control
sns.barplot(data=status_counts, x="admission_term_y", y="count", hue="status", ax=ax)
ax.set_title("Cohort Outcomes by Admission Term")
ax.set_ylabel("Count of Students")
st.pyplot(fig, use_container_width=True)  # Ensure the plot fits well in Streamlit

# --- Plot 2: GPA Distribution by Cohort ---
st.subheader("GPA Distribution by Cohort")
fig, ax = plt.subplots(figsize=(10, 6))  # Adjusted size for better control
sns.kdeplot(data=merged_df[merged_df["gpa_y"] > 0], x="gpa_y", hue="admission_term_y", fill=True, ax=ax)
ax.set_title("GPA Distribution by Cohort")
st.pyplot(fig, use_container_width=True)  # Ensure the plot fits well in Streamlit

# --- Plot 3: Graduation Timing ---
st.subheader("Graduation Timing")
grad_timing = merged_df[merged_df["graduated_y"]].groupby("graduation_semester").size()
fig, ax = plt.subplots(figsize=(10, 6))  # Adjusted size for better control
grad_timing.plot(kind="bar", color="green", ax=ax)
ax.set_title("Graduates by Semester of Completion")
ax.set_xlabel("Graduation Semester")
ax.set_ylabel("Number of Students")
st.pyplot(fig, use_container_width=True)  # Ensure the plot fits well in Streamlit

# --- Visualization: Student Progression by Semester (Interactive View) ---
st.subheader("Student Progression Visualization")

# Create an empty DataFrame to represent student progress across semesters
student_progress = []

# Loop through each student's data in the merged dataset
for _, student in merged_df.iterrows():
    student_row = []
    for semester in range(1, 13):  # Loop through semesters 1 to 12
        courses = student['study_plan'].get(str(semester), [])
        status = 'Enrolled' if courses else 'Not Enrolled'
        
        # Use '_y' suffix for graduation and dropout status
        if student['graduated_y']:  # Use graduated_y
            status = 'Graduated'
        elif student['dropped_out_y']:  # Use dropped_out_y
            status = 'Dropped Out'
        
        student_row.append(status)

    student_progress.append(student_row)

# Convert list to DataFrame
progress_df = pd.DataFrame(student_progress, columns=[f"Semester {i}" for i in range(1, 13)])

# Display the heatmap with progress information
st.dataframe(progress_df)

# Plotting an interactive heatmap to show student progression across semesters
fig, ax = plt.subplots(figsize=(14, 10))
sns.heatmap(progress_df == 'Graduated', annot=True, cmap="Greens", cbar=False, ax=ax)
ax.set_title("Graduation Status (Green)")
st.pyplot(fig)

# --- Extra Option: Download Results ---
st.subheader("Export Results")
st.download_button(
    label="Download results as CSV",
    data=merged_df.to_csv(index=False).encode("utf-8"),
    file_name="merged_simulation_results.csv",
    mime="text/csv",
)
