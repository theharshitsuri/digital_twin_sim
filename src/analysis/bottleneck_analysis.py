import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json
from collections import Counter

def analyze_bottlenecks():
    """
    Deep dive analysis of course bottlenecks and prerequisite issues.
    Run this after your main simulation completes.
    """
    
    print("="*70)
    print("BOTTLENECK ANALYSIS REPORT")
    print("="*70)
    
    # Load data
    try:
        blocked_df = pd.read_csv("data/blocked_courses.csv")
        students_df = pd.read_csv("data/student_outcomes.csv")
        with open("data/course_catalog.json", "r") as f:
            catalog = json.load(f)
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("Please run the main simulation first!")
        return
    
    if len(blocked_df) == 0:
        print("✅ No course blockages detected! All students progressed smoothly.")
        return
    
    # === SECTION 1: Most Problematic Courses ===
    print("\n" + "="*70)
    print("1. COURSES CAUSING THE MOST DELAYS")
    print("="*70)
    
    course_blocks = blocked_df.groupby('blocked_course').agg({
        'student_id': 'count',
        'semester': 'mean',
        'student_gpa': 'mean',
        'student_graduated': lambda x: (x.sum() / len(x) * 100)
    }).round(2)
    course_blocks.columns = ['Total Blockages', 'Avg Semester Blocked', 'Avg GPA of Blocked', 'Grad Rate %']
    course_blocks = course_blocks.sort_values('Total Blockages', ascending=False)
    
    print("\nTop 15 Most Frequently Blocked Courses:")
    print(course_blocks.head(15))
    
    # Add course names
    print("\nWith Course Names:")
    for course in course_blocks.head(10).index:
        info = catalog.get(course, {})
        blocks = course_blocks.loc[course, 'Total Blockages']
        avg_sem = course_blocks.loc[course, 'Avg Semester Blocked']
        grad_rate = course_blocks.loc[course, 'Grad Rate %']
        print(f"   {course:12s} {info.get('name', 'Unknown'):45s} "
              f"| {blocks:4.0f} blocks | Sem {avg_sem:.1f} | {grad_rate:.1f}% grad")
    
    # === SECTION 2: Prerequisite Chains ===
    print("\n" + "="*70)
    print("2. PREREQUISITE BOTTLENECKS (Courses Blocking Others)")
    print("="*70)
    
    prereq_blocks = Counter()
    for prereqs in blocked_df['missing_prereqs'].dropna():
        if prereqs:
            prereq_blocks.update(prereqs.split(', '))
    
    print("\nTop 15 Prerequisites Causing Blockages:")
    for prereq, count in prereq_blocks.most_common(15):
        info = catalog.get(prereq, {})
        print(f"   {prereq:12s} {info.get('name', 'Unknown'):45s} | {count:4d} times")
    
    # === SECTION 3: Timing Analysis ===
    print("\n" + "="*70)
    print("3. WHEN DO BLOCKAGES OCCUR? (By Semester)")
    print("="*70)
    
    semester_blocks = blocked_df.groupby('semester').size()
    print(semester_blocks)
    
    # === SECTION 4: Term-Specific Issues ===
    print("\n" + "="*70)
    print("4. BLOCKAGES BY ACADEMIC TERM")
    print("="*70)
    
    term_blocks = blocked_df.groupby('term').size().sort_values(ascending=False)
    print(term_blocks)
    print(f"\nInterpretation: If Summer has few blockages, students aren't "
          f"taking many courses then (expected).")
    
    # === SECTION 5: Student Impact ===
    print("\n" + "="*70)
    print("5. STUDENT-LEVEL IMPACT")
    print("="*70)
    
    # Group students by blocking severity
    blocking_bins = [0, 1, 3, 5, 10, 100]
    labels = ['Never', '1-2 times', '3-4 times', '5-9 times', '10+ times']
    students_df['blocking_category'] = pd.cut(
        students_df['num_times_blocked'], 
        bins=blocking_bins, 
        labels=labels, 
        include_lowest=True
    )
    
    impact = students_df.groupby('blocking_category').agg({
        'id': 'count',
        'graduated': 'sum',
        'dropped_out': 'sum',
        'gpa': 'mean',
        'semesters_enrolled': 'mean'
    }).round(2)
    impact.columns = ['Students', 'Graduated', 'Dropped', 'Avg GPA', 'Avg Semesters']
    impact['Grad Rate %'] = (impact['Graduated'] / impact['Students'] * 100).round(1)
    
    print(impact)
    
    # === SECTION 6: Critical Paths ===
    print("\n" + "="*70)
    print("6. PREREQUISITE CHAINS CAUSING CASCADING DELAYS")
    print("="*70)
    
    # Find courses that are both blocked AND block others
    blocked_courses = set(blocked_df['blocked_course'].unique())
    blocking_prereqs = set()
    for prereqs in blocked_df['missing_prereqs'].dropna():
        if prereqs:
            blocking_prereqs.update(prereqs.split(', '))
    
    critical_courses = blocked_courses & blocking_prereqs
    
    print(f"\n{len(critical_courses)} courses are in critical prerequisite chains:")
    print("(These courses are blocked themselves AND block other courses)")
    for course in sorted(critical_courses):
        info = catalog.get(course, {})
        blocks_this = len(blocked_df[blocked_df['blocke