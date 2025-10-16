import streamlit as st
import pandas as pd
import json
import plotly.graph_objects as go
import numpy as np

# --- Page Config ---
st.set_page_config(page_title="Digital Twin - Course Heatmap", layout="wide")
st.title("🎓 Student Course Progression Heatmap")

# --- Load Data ---
@st.cache_data
def load_data():
    try:
        with open("data/course_catalog.json", "r") as f:
            course_catalog = json.load(f)
        student_outcomes = pd.read_csv("data/student_outcomes.csv")
        return course_catalog, student_outcomes
    except FileNotFoundError as e:
        st.error(f"Missing file: {e.filename}")
        st.stop()

course_catalog, student_outcomes = load_data()

# Check if transcript column exists
if 'transcript' not in student_outcomes.columns:
    st.error("""
    ❌ **Transcript data not found!**
    
    Your simulation needs to save transcript data. Update your simulation code to include:
    
    ```python
    student_records.append({
        ...
        "transcript": student.transcript,  # Add this line
        ...
    })
    ```
    
    Then re-run your simulation.
    """)
    st.stop()

# Parse transcript JSON strings - they're stored as strings in CSV
def parse_transcript(transcript_str):
    if pd.isna(transcript_str):
        return {}
    if isinstance(transcript_str, dict):
        return transcript_str
    try:
        # Remove quotes and parse the string representation of dict
        return eval(transcript_str) if isinstance(transcript_str, str) else {}
    except:
        return {}

student_outcomes['transcript_parsed'] = student_outcomes['transcript'].apply(parse_transcript)

# --- Organize Courses by Category ---
course_order = []
categories = [
    "Gen Ed", 
    "Math", 
    "Science", 
    "Science Elective",
    "Engineering",
    "CS Core", 
    "Theory Elective",
    "Software Elective", 
    "Technical Elective",
    "Capstone",
    "Capstone/Elective"
]

for category in categories:
    courses_in_cat = [code for code, info in course_catalog.items() 
                      if info.get("category") == category]
    course_order.extend(sorted(courses_in_cat))

# --- Sidebar Filters ---
st.sidebar.header("Filters")

# Admission term filter
admission_terms = student_outcomes['admission_term'].unique()
selected_terms = st.sidebar.multiselect(
    "Admission Term", 
    admission_terms, 
    default=list(admission_terms)
)

# Status filter
status_filter = st.sidebar.multiselect(
    "Student Status",
    ["Graduated", "Dropped Out", "Enrolled"],
    default=["Graduated", "Enrolled"]
)

# Sort options
sort_by = st.sidebar.selectbox(
    "Sort Students By",
    ["GPA (Descending)", "GPA (Ascending)", "Credits Completed", "Student ID"]
)

# Limit display
max_students = st.sidebar.slider("Max Students to Display", 10, 500, 100)

# --- Filter Students ---
filtered_outcomes = student_outcomes[
    student_outcomes['admission_term'].isin(selected_terms)
].copy()

# Apply status filter
status_mask = pd.Series([False] * len(filtered_outcomes), index=filtered_outcomes.index)
if "Graduated" in status_filter:
    status_mask |= filtered_outcomes['graduated']
if "Dropped Out" in status_filter:
    status_mask |= filtered_outcomes['dropped_out']
if "Enrolled" in status_filter:
    status_mask |= (~filtered_outcomes['graduated'] & ~filtered_outcomes['dropped_out'])

filtered_outcomes = filtered_outcomes[status_mask].reset_index(drop=True)

# --- Sort Students ---
if sort_by == "GPA (Descending)":
    filtered_outcomes = filtered_outcomes.sort_values('gpa', ascending=False)
elif sort_by == "GPA (Ascending)":
    filtered_outcomes = filtered_outcomes.sort_values('gpa', ascending=True)
elif sort_by == "Credits Completed":
    filtered_outcomes = filtered_outcomes.sort_values('credits_completed', ascending=False)
else:
    filtered_outcomes = filtered_outcomes.sort_values('id')

# Total students info
total_students = len(filtered_outcomes)
st.sidebar.info(f"Total students: {total_students}")

# Option: Load all or paginate
view_mode = st.sidebar.radio("View Mode", ["Show All (Scrollable)", "Paginated View"])

if view_mode == "Paginated View":
    st.sidebar.markdown("### Navigate Students")
    students_per_page = st.sidebar.slider("Students per page", 10, 100, 50)
    start_idx = st.sidebar.number_input("Start from student #", 0, max(0, total_students - students_per_page), 0, step=students_per_page)
    end_idx = min(start_idx + students_per_page, total_students)
    st.sidebar.info(f"Showing students {start_idx} to {end_idx}")
    filtered_outcomes = filtered_outcomes.iloc[start_idx:end_idx]
else:
    # Limit to reasonable number for performance
    max_for_scroll = st.sidebar.slider("Max students to load", 50, 500, 200)
    if total_students > max_for_scroll:
        st.warning(f"Showing first {max_for_scroll} of {total_students} students for performance")
        filtered_outcomes = filtered_outcomes.head(max_for_scroll)

# --- Build Heatmap Matrix ---
grade_to_num = {"A": 4.0, "B": 3.0, "C": 2.0, "D": 1.0, "F": 0.5, "Not Taken": 0}
grade_colors = {
    0: "#1a1a1a",      # Not taken - black
    0.5: "#8B0000",    # F - dark red
    1.0: "#FFB6C1",    # D - light pink
    2.0: "#90EE90",    # C - light green
    3.0: "#32CD32",    # B - medium green
    4.0: "#006400"     # A - dark green
}

# Create matrix
matrix = []
hover_text = []
student_labels = []

for _, student_row in filtered_outcomes.iterrows():
    student_id = student_row['id']
    transcript = student_row.get('transcript_parsed', {})
    
    # If transcript is empty or not a dict, skip
    if not isinstance(transcript, dict) or not transcript:
        continue
    
    # Build row for this student
    student_grades = []
    student_hover = []
    
    for course in course_order:
        grade = transcript.get(course, "Not Taken")
        grade_val = grade_to_num.get(grade, 0)
        student_grades.append(grade_val)
        
        # Hover text
        course_name = course_catalog[course]['name']
        hover_info = f"Student {student_id}<br>{course}: {course_name}<br>Grade: {grade}<br>GPA: {student_row['gpa']:.2f}"
        student_hover.append(hover_info)
    
    matrix.append(student_grades)
    hover_text.append(student_hover)
    
    # Label with status emoji
    status = "🎓" if student_row['graduated'] else ("❌" if student_row['dropped_out'] else "📚")
    student_labels.append(f"{status} ID:{student_id} (GPA:{student_row['gpa']:.2f})")

# --- Create Plotly Heatmap ---
if matrix:
    fig = go.Figure(data=go.Heatmap(
        z=list(zip(*matrix)),  # Transpose the matrix
        x=student_labels,  # Students on X-axis
        y=course_order,  # Courses on Y-axis
        hovertext=list(zip(*hover_text)),  # Transpose hover text
        hoverinfo='text',
        colorscale=[
            [0.0, grade_colors[0]],     # Not taken
            [0.125, grade_colors[0.5]], # F
            [0.25, grade_colors[1.0]],  # D
            [0.5, grade_colors[2.0]],   # C
            [0.75, grade_colors[3.0]],  # B
            [1.0, grade_colors[4.0]]    # A
        ],
        zmin=0,
        zmax=4,
        colorbar=dict(
            title="Grade",
            tickvals=[0, 0.5, 1.0, 2.0, 3.0, 4.0],
            ticktext=["Not Taken", "F", "D", "C", "B", "A"]
        )
    ))
    
    # Adjust layout based on view mode
    if view_mode == "Show All (Scrollable)":
        chart_width = len(matrix) * 15  # Narrower columns for more students
        chart_height = 900
        use_container = False
    else:
        chart_width = 1600
        chart_height = 1000
        use_container = True
    
    fig.update_layout(
        title=f"Student Course Performance Matrix ({len(matrix)} students)",
        xaxis_title="Students (Use pan/zoom tools to navigate →)",
        yaxis_title="Courses (Ordered by Category)",
        height=chart_height,
        width=chart_width,
        xaxis=dict(
            tickangle=-90, 
            tickfont=dict(size=8),
            side='bottom',
            rangeslider=dict(visible=False)
        ),
        yaxis=dict(
            tickfont=dict(size=10),
            fixedrange=False  # Allow zoom
        ),
        hoverlabel=dict(bgcolor="white", font_size=12),
        margin=dict(l=150, r=50, t=80, b=150),
        dragmode='pan'  # Enable panning by default
    )
    
    # Configure with pan and zoom tools
    config = {
        'scrollZoom': True,
        'displayModeBar': True,
        'modeBarButtonsToAdd': ['pan2d', 'zoom2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d'],
        'modeBarButtonsToRemove': ['lasso2d', 'select2d']
    }
    
    st.plotly_chart(fig, use_container_width=use_container, config=config)
    
    # --- Summary Stats ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Students", len(filtered_outcomes))
    with col2:
        st.metric("Avg GPA", f"{filtered_outcomes['gpa'].mean():.2f}")
    with col3:
        st.metric("Graduated", filtered_outcomes['graduated'].sum())
    with col4:
        st.metric("Dropped Out", filtered_outcomes['dropped_out'].sum())
    
    # --- Legend ---
    st.markdown("### Legend")
    st.markdown("""
    - **Black**: Course not taken
    - **Dark Red**: Failed (F)
    - **Light Pink**: D grade
    - **Light Green**: C grade
    - **Medium Green**: B grade
    - **Dark Green**: A grade
    
    **Student Status:**
    - 🎓 = Graduated
    - ❌ = Dropped Out
    - 📚 = Currently Enrolled
    """)
    
else:
    st.warning("No students match the selected filters.")

# --- Download Button ---
if not filtered_outcomes.empty:
    st.download_button(
        label="📥 Download Filtered Student Data",
        data=filtered_outcomes.to_csv(index=False).encode("utf-8"),
        file_name="filtered_students.csv",
        mime="text/csv"
    )