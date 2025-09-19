import json
import random
import os

# Reproducibility
random.seed(42)

def generate_student(student_id, admission_term, course_catalog, core_courses):
    """
    Generate a synthetic student profile with study plan & attributes.
    Ensures that all CS Core courses are included in the study plan.
    Simulation will fill transcript, GPA, graduation, dropout, etc.
    """
    study_plan = {}
    completed = set()
    semester_num = 1

    # Student profile
    academic_ability = round(random.uniform(0.5, 0.95), 2)
    dropout_chance = round(random.uniform(0.05, 0.2), 2)

    # Target: ~40 courses (~120 credits)
    total_courses_target = 40

    # Track which core courses remain
    remaining_core = core_courses.copy()
    random.shuffle(remaining_core)

    while len(completed) < total_courses_target and semester_num <= 12:
        semester_courses = []
        credits_this_sem = 0

        # Priority: take core courses first if any remain
        if remaining_core:
            candidates = [
                (c, course_catalog[c]) for c in remaining_core if c not in completed
            ]
        else:
            # Otherwise, take from the full catalog
            candidates = [
                (c, info) for c, info in course_catalog.items() if c not in completed
            ]

        random.shuffle(candidates)

        # Allow 3–5 courses per semester
        max_courses = random.choice([3, 4, 5])

        for course_code, info in candidates:
            if len(semester_courses) >= max_courses:
                break
            credits = info.get("credits", 3)
            if credits_this_sem + credits > 15:
                continue

            semester_courses.append(course_code)
            completed.add(course_code)
            credits_this_sem += credits

            if course_code in remaining_core:
                remaining_core.remove(course_code)

        if semester_courses:
            study_plan[str(semester_num)] = semester_courses

        semester_num += 1

    return {
        "id": student_id,
        "academic_ability": academic_ability,
        "dropout_chance": dropout_chance,
        "admission_term": admission_term,
        "study_plan": study_plan,
        "credits_completed": 0,       # start empty
        "graduated": False,
        "dropped_out": False,
        "transcript": {},
        "completed_courses": [],
        "current_courses": [],
        "repeat_courses": [],
        "gpa": 0.0
    }

def generate_students(course_catalog, num_per_term=1000):
    """Generate synthetic students across Fall, Spring, Summer with study plans."""
    students = []
    student_id = 1
    terms = ["Fall", "Spring", "Summer"]

    # Identify core CS courses (must be passed for graduation)
    core_courses = [c for c, info in course_catalog.items() if info["category"] == "CS Core"]

    for term in terms:
        for _ in range(num_per_term):
            students.append(generate_student(student_id, term, course_catalog, core_courses))
            student_id += 1

    return students

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)

    # Load course catalog
    with open("data/course_catalog.json", "r") as f:
        course_catalog = json.load(f)

    synthetic_students = generate_students(course_catalog, num_per_term=1000)

    with open("data/synthetic_students.json", "w") as f:
        json.dump(synthetic_students, f, indent=2)

    print(f"✅ Generated {len(synthetic_students)} synthetic students with CS Core courses included in study plans")
    print("Saved to data/synthetic_students.json")
