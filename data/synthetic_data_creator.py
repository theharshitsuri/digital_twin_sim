import json
import random
import os

# Reproducibility
random.seed(42)

def sat_to_ability_and_gpa(sat_score: int):
    """
    Map SAT score (900–1450) into academic_ability (0.5–0.95)
    and predicted GPA (1.5–4.0).
    """
    normalized = (sat_score - 900) / (1450 - 900)  # normalize to 0–1
    academic_ability = round(0.5 + normalized * 0.45, 2)
    predicted_gpa = round(1.5 + normalized * 2.5, 2)
    return academic_ability, predicted_gpa

def generate_student(student_id, admission_term, course_catalog, core_courses):
    """
    Generate a synthetic student profile with SAT-based ability & study plan.
    Ensures that all CS Core courses are included in the study plan.
    Course loads vary: Fall/Spring = 4–6, Summer = 0–2.
    """
    study_plan = {}
    completed = set()
    semester_num = 1

    # 🎯 SAT-driven ability
    sat_score = random.randint(900, 1450)
    academic_ability, predicted_gpa = sat_to_ability_and_gpa(sat_score)

    dropout_chance = round(random.uniform(0.05, 0.2), 2)

    # Cohort info
    start_term = admission_term
    started_in_fall = (admission_term == "Fall")

    # Target: ~40 courses (~120 credits)
    total_courses_target = 40

    # Track which core courses remain
    remaining_core = core_courses.copy()
    random.shuffle(remaining_core)

    # Define the rotation of academic terms based on admission term
    term_order = {
        "Fall":    ["Fall", "Spring", "Summer"],
        "Spring":  ["Spring", "Summer", "Fall"],
        "Summer":  ["Summer", "Fall", "Spring"]
    }[admission_term]

    while len(completed) < total_courses_target and semester_num <= 12:
        semester_courses = []
        credits_this_sem = 0

        # Which academic term is this semester?
        current_term = term_order[(semester_num - 1) % 3]

        # --- Course load rules ---
        if current_term == "Summer":
            # Summer can be 0, 1, or 2 courses
            target_courses = random.choice([0, 1, 2])
            min_courses, max_courses = 0, target_courses
        else:
            # Fall/Spring always 4–6 courses
            target_courses = random.choice([4, 5, 6])
            min_courses, max_courses = 4, target_courses

        # Priority: take core courses first if any remain
        if remaining_core:
            candidates = [
                (c, course_catalog[c]) for c in remaining_core if c not in completed
            ]
        else:
            candidates = [
                (c, info) for c, info in course_catalog.items() if c not in completed
            ]

        random.shuffle(candidates)

        for course_code, info in candidates:
            if len(semester_courses) >= max_courses:
                break
            credits = info.get("credits", 3)
            if credits_this_sem + credits > 18:  # cap at 18 credits
                continue

            semester_courses.append(course_code)
            completed.add(course_code)
            credits_this_sem += credits

            if course_code in remaining_core:
                remaining_core.remove(course_code)

        # Guarantee: keep Fall/Spring semesters if they meet min_courses
        if current_term in ["Fall", "Spring"]:
            if len(semester_courses) < min_courses:
                # Fill with random electives until min requirement
                extras = [
                    c for c in course_catalog.keys()
                    if c not in completed and c not in semester_courses
                ]
                random.shuffle(extras)
                for extra in extras:
                    if len(semester_courses) >= min_courses:
                        break
                    semester_courses.append(extra)
                    completed.add(extra)

        # Add semester if it has any courses (or meets min requirement)
        if semester_courses:
            study_plan[str(semester_num)] = semester_courses

        semester_num += 1

    return {
        "id": student_id,
        "sat_score": sat_score,
        "predicted_gpa": predicted_gpa,
        "academic_ability": academic_ability,
        "dropout_chance": dropout_chance,
        "admission_term": admission_term,
        "start_term": start_term,
        "started_in_fall": started_in_fall,
        "study_plan": study_plan,
        "credits_completed": 0,
        "graduated": False,
        "dropped_out": False,
        "transcript": {},
        "completed_courses": [],
        "current_courses": [],
        "repeat_courses": [],
        "gpa": 0.0
    }

def generate_students(course_catalog, num_per_term=1000):
    """Generate synthetic students across Fall, Spring, Summer with SAT scores."""
    students = []
    student_id = 0
    terms = ["Fall", "Spring", "Summer"]

    core_courses = [c for c, info in course_catalog.items() if info["category"] == "CS Core"]

    for term in terms:
        for _ in range(num_per_term):
            students.append(generate_student(student_id, term, course_catalog, core_courses))
            student_id += 1

    return students

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)

    with open("data/course_catalog.json", "r") as f:
        course_catalog = json.load(f)

    synthetic_students = generate_students(course_catalog, num_per_term=1000)

    with open("data/synthetic_students.json", "w") as f:
        json.dump(synthetic_students, f, indent=2)

    print(f"✅ Generated {len(synthetic_students)} synthetic students with SAT-based GPA prediction")
    print("Saved to data/synthetic_students.json")
