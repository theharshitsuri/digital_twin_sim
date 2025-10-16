"""
import json
import matplotlib.pyplot as plt
import pandas as pd
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

    # Run for up to 12 semesters (6 years)
    for _ in range(12):
        if not bscs_model.running:
            break
        bscs_model.step()

    # Collect aggregate results
    results = bscs_model.datacollector.get_model_vars_dataframe()
    results.index.name = "Semester"
    results.to_csv("data/results.csv")

    print("Simulation finished ✅")
    print(results.tail(1))  # Final snapshot

    # --- NEW: Save detailed per-student outcomes ---
    student_records = []
    for student in bscs_model.schedule.agents:
        student_records.append({
            "id": student.unique_id,
            "credits_completed": student.credits_completed,
            "gpa": student.gpa,
            "graduated": student.graduated,
            "dropped_out": student.drop_out,
            "semesters_enrolled": student.semesters_enrolled,
        })

    df = pd.DataFrame(student_records)
    df.to_csv("data/student_outcomes.csv", index=False)
    print("✅ Saved detailed student outcomes to data/student_outcomes.csv")

    # Plot macro results
    results.plot()
    plt.title("Student Progression Over Time")
    plt.xlabel("Semester")
    plt.ylabel("Number of Students")
    plt.show()
"""
import json
import matplotlib.pyplot as plt
import pandas as pd
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

    # Run for up to 14 semesters
    for _ in range(14):
        if not bscs_model.running:
            break
        bscs_model.step()

    # Collect aggregate results
    results = bscs_model.datacollector.get_model_vars_dataframe()
    results.index.name = "Semester"
    results.to_csv("data/results.csv")

    print("Simulation finished ✅")
    print(results.tail(1))  # Final snapshot

    # --- Save detailed per-student outcomes ---
    student_records = []
    for student, profile in zip(bscs_model.schedule.agents, students_data):
        student_records.append({
    "id": student.unique_id,
    "credits_completed": student.credits_completed,
    "gpa": student.gpa,
    "graduated": student.graduated,
    "dropped_out": student.dropped_out,
    "semesters_enrolled": student.semester_num - 1,
    "graduation_semester": getattr(student, "graduation_semester", None),
    "admission_term": profile.get("admission_term"),
    "started_in_fall": profile.get("started_in_fall"),
    # ADD THESE:
    "transcript": student.transcript,  # Course grades!
    "completed_courses": list(student.completed_courses),
    "sat_score": profile.get("sat_score"),
    "academic_ability": profile.get("academic_ability")
})

    df = pd.DataFrame(student_records)
    df.to_csv("data/student_outcomes.csv", index=False)
    print("✅ Saved detailed student outcomes to data/student_outcomes.csv")

    # --- Extra Analysis: Graduates by semester count ---
    grad_counts = (
        df[df["graduated"]]
        .groupby("graduation_semester")
        .size()
        .reindex([10, 11, 12, 13, 14], fill_value=0)
    )
    print("\nGraduation Timing:")
    for sem, count in grad_counts.items():
        print(f" → Graduated in {sem} semesters: {count}")

    # --- Extra Analysis: Cohort Outcomes ---
    cohort_stats = df.groupby("admission_term")[["graduated", "dropped_out"]].sum()
    cohort_stats["still_enrolled"] = (
        df.groupby("admission_term").size() - cohort_stats["graduated"] - cohort_stats["dropped_out"]
    )
    print("\nCohort Outcomes (by Admission Term):")
    print(cohort_stats)

    # Plot macro results
    results.plot()
    plt.title("Student Progression Over Time")
    plt.xlabel("Semester")
    plt.ylabel("Number of Students")
    plt.show()
