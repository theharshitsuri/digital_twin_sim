import json
import matplotlib.pyplot as plt
import pandas as pd
from collections import Counter
from src.model.university_model import UniversityModel

if __name__ == "__main__":
    # Load synthetic students (JSON file you generated earlier)
    with open("data/synthetic_students.json", "r") as f:
        students_data = json.load(f)
    
    # Load course catalog (JSON file we created)
    with open("data/course_catalog.json", "r") as f:
        course_catalog = json.load(f)
    
    # Initialize model
    bscs_model = UniversityModel(
        students_data=students_data,
        course_catalog=course_catalog,
        required_credits=120
    )
    
    print("🚀 Starting simulation...")
    print(f"   Initial students: {len(students_data)}")
    print(f"   Required credits: 120")
    print(f"   CS Core courses: {len(bscs_model.core_courses)}")
    print()
    
    # Run for up to 14 semesters
    for step_num in range(14):
        if not bscs_model.running:
            print(f"✅ Simulation ended early at semester {step_num}")
            break
        bscs_model.step()
        
        # Progress updates every 2 semesters
        if (step_num + 1) % 2 == 0:
            enrolled = bscs_model.count_enrolled()
            graduated = bscs_model.count_graduated()
            dropped = bscs_model.count_dropped_out()
            print(f"Semester {step_num + 1} ({bscs_model.current_term}): "
                  f"Enrolled={enrolled}, Graduated={graduated}, Dropped={dropped}")
    
    print("\n" + "="*60)
    print("SIMULATION COMPLETE")
    print("="*60)
    
    # Collect aggregate results
    results = bscs_model.datacollector.get_model_vars_dataframe()
    results.index.name = "Step"
    results.to_csv("data/results.csv")
    print("\n✅ Saved time-series results to data/results.csv")
    
    # --- Save detailed per-student outcomes ---
    student_records = []
    all_blocked_courses = []  # 🆕 Collect all blockages for analysis
    
    for student, profile in zip(bscs_model.schedule.agents, students_data):
        # Basic student record
        record = {
            "id": student.unique_id,
            "credits_completed": student.credits_completed,
            "gpa": student.gpa,
            "graduated": student.graduated,
            "dropped_out": student.dropped_out,
            "semesters_enrolled": student.semester_num - 1,
            "graduation_semester": getattr(student, "graduation_semester", None),
            "admission_term": profile.get("admission_term"),
            "started_in_fall": profile.get("started_in_fall"),
            "transcript": student.transcript,
            "completed_courses": list(student.completed_courses),
            "sat_score": profile.get("sat_score"),
            "academic_ability": profile.get("academic_ability"),
            # 🆕 Blocking metrics
            "blocked_courses": student.blocked_courses,
            "num_times_blocked": len(student.blocked_courses),
            "unique_blocked_courses": len(set(b['course'] for b in student.blocked_courses))
        }
        student_records.append(record)
        
        # 🆕 Collect individual blockages for aggregate analysis
        for block in student.blocked_courses:
            all_blocked_courses.append({
                'student_id': student.unique_id,
                'semester': block['semester'],
                'term': block['term'],
                'blocked_course': block['course'],
                'missing_prereqs': ', '.join(block['missing_prereqs']),
                'student_gpa': student.gpa,
                'student_ability': student.academic_ability,
                'student_graduated': student.graduated
            })
    
    df = pd.DataFrame(student_records)
    df.to_csv("data/student_outcomes.csv", index=False)
    print("✅ Saved detailed student outcomes to data/student_outcomes.csv")
    
    # 🆕 Save blocked courses analysis
    if all_blocked_courses:
        blocked_df = pd.DataFrame(all_blocked_courses)
        blocked_df.to_csv("data/blocked_courses.csv", index=False)
        print("✅ Saved blocked courses analysis to data/blocked_courses.csv")
    
    # --- Analysis: Graduation Timing ---
    print("\n" + "="*60)
    print("GRADUATION TIMING")
    print("="*60)
    grad_counts = (
        df[df["graduated"]]
        .groupby("graduation_semester")
        .size()
        .reindex(range(10, 15), fill_value=0)
    )
    for sem, count in grad_counts.items():
        print(f"   Graduated in {sem} semesters: {count:4d} students")
    
    avg_grad_time = df[df["graduated"]]["graduation_semester"].mean()
    print(f"\n   Average graduation time: {avg_grad_time:.2f} semesters")
    
    # --- Analysis: Cohort Outcomes ---
    print("\n" + "="*60)
    print("COHORT OUTCOMES (by Admission Term)")
    print("="*60)
    cohort_stats = df.groupby("admission_term")[["graduated", "dropped_out"]].sum()
    cohort_stats["still_enrolled"] = (
        df.groupby("admission_term").size() - cohort_stats["graduated"] - cohort_stats["dropped_out"]
    )
    cohort_stats["total"] = df.groupby("admission_term").size()
    cohort_stats["grad_rate"] = (cohort_stats["graduated"] / cohort_stats["total"] * 100).round(1)
    print(cohort_stats)
    
    # 🆕 --- Analysis: Bottleneck Courses ---
    if all_blocked_courses:
        print("\n" + "="*60)
        print("TOP 10 BOTTLENECK COURSES (Most Frequently Blocked)")
        print("="*60)
        blocked_counter = Counter(b['blocked_course'] for b in all_blocked_courses)
        for course, count in blocked_counter.most_common(10):
            course_name = course_catalog.get(course, {}).get('name', 'Unknown')
            print(f"   {course:12s} ({course_name:40s}): {count:4d} blockages")
        
        print("\n" + "="*60)
        print("TOP 10 MISSING PREREQUISITES (Most Common Blockers)")
        print("="*60)
        prereq_counter = Counter()
        for b in all_blocked_courses:
            prereqs = b['missing_prereqs'].split(', ') if b['missing_prereqs'] else []
            prereq_counter.update(prereqs)
        
        for prereq, count in prereq_counter.most_common(10):
            prereq_name = course_catalog.get(prereq, {}).get('name', 'Unknown')
            print(f"   {prereq:12s} ({prereq_name:40s}): {count:4d} times")
    
    # 🆕 --- Analysis: Blocking Impact ---
    print("\n" + "="*60)
    print("BLOCKING IMPACT ON GRADUATION")
    print("="*60)
    
    # Students who were never blocked
    never_blocked = df[df['num_times_blocked'] == 0]
    grad_rate_no_block = (never_blocked['graduated'].sum() / len(never_blocked) * 100) if len(never_blocked) > 0 else 0
    
    # Students who were blocked
    blocked = df[df['num_times_blocked'] > 0]
    grad_rate_blocked = (blocked['graduated'].sum() / len(blocked) * 100) if len(blocked) > 0 else 0
    
    print(f"   Students never blocked: {len(never_blocked):4d} (grad rate: {grad_rate_no_block:.1f}%)")
    print(f"   Students blocked 1+ times: {len(blocked):4d} (grad rate: {grad_rate_blocked:.1f}%)")
    
    if len(blocked) > 0:
        avg_blocks = blocked['num_times_blocked'].mean()
        print(f"   Average blockages per affected student: {avg_blocks:.2f}")
    
    # --- Visualization ---
    print("\n📊 Generating plots...")
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Plot 1: Student progression over time
    results[['Enrolled', 'Graduated', 'DroppedOut']].plot(ax=axes[0, 0])
    axes[0, 0].set_title("Student Progression Over Time")
    axes[0, 0].set_xlabel("Semester")
    axes[0, 0].set_ylabel("Number of Students")
    axes[0, 0].legend(['Enrolled', 'Graduated', 'Dropped Out'])
    
    # Plot 2: GPA trend
    results['AvgGPA'].plot(ax=axes[0, 1], color='green')
    axes[0, 1].set_title("Average GPA Over Time")
    axes[0, 1].set_xlabel("Semester")
    axes[0, 1].set_ylabel("GPA")
    axes[0, 1].set_ylim([0, 4.0])
    
    # Plot 3: Graduation timing distribution
    grad_counts.plot(kind='bar', ax=axes[1, 0], color='skyblue')
    axes[1, 0].set_title("Graduation Timing Distribution")
    axes[1, 0].set_xlabel("Semester")
    axes[1, 0].set_ylabel("Number of Graduates")
    axes[1, 0].set_xticklabels(axes[1, 0].get_xticklabels(), rotation=0)
    
    # Plot 4: 🆕 Blocked courses over time
    if 'TotalBlocked' in results.columns:
        results['TotalBlocked'].plot(ax=axes[1, 1], color='red')
        axes[1, 1].set_title("Course Blockages Over Time")
        axes[1, 1].set_xlabel("Semester")
        axes[1, 1].set_ylabel("Number of Blockages")
    
    plt.tight_layout()
    plt.savefig("data/simulation_results.png", dpi=300, bbox_inches='tight')
    print("✅ Saved visualization to data/simulation_results.png")
    plt.show()
    
    print("\n" + "="*60)
    print("ALL OUTPUTS SAVED TO data/ DIRECTORY")
    print("="*60)