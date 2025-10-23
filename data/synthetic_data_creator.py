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

def get_elective_from_category(course_catalog, category, completed, exclude_labs=False):
    """
    Get a random course from a specific category that hasn't been completed.
    If exclude_labs is True, filter out lab courses (courses ending in 'L').
    """
    candidates = [
        code for code, info in course_catalog.items()
        if info["category"] == category and code not in completed
    ]
    
    # Filter out lab courses if requested
    if exclude_labs:
        candidates = [c for c in candidates if not c.endswith('L')]
    
    return random.choice(candidates) if candidates else None

def generate_study_plan_from_template(course_catalog, admission_term):
    """
    Generate study plan following USF's exact 4-year plan structure.
    For Fall admission: semesters 1-11 directly
    For Spring admission: offset by +1  
    For Summer admission: offset by +2
    """
    
    # Base template follows the USF 4-year plan (Fall start)
    base_template = {
        1: {  # Fall - Semester 1
            "required": ["CIS 1930", "COP 2510", "ENC 1101", "MAC 2311"],
            "electives": [("Natural Science Elective (no lab)", "Science Elective")]
        },
        2: {  # Spring - Semester 2
            "required": ["COP 3514", "ENC 1102", "MAC 2312", "PHY 2048", "PHY 2048L"],
            "electives": []
        },
        3: {  # Summer - Semester 3
            "required": [],
            "electives": []  # Optional summer - always empty
        },
        4: {  # Fall - Semester 4
            "required": ["CDA 3201", "CDA 3201L", "COP 4530"],
            "electives": [("General/Unrestricted Elective", "General Elective"),
                         ("General/Unrestricted Elective", "General Elective")]
        },
        5: {  # Spring - Semester 5
            "required": ["CDA 3103", "COT 3100", "PHY 2049", "PHY 2049L"],
            "electives": [("Gen-Ed State Humanities (SGEH)", "Gen Ed Humanities")]
        },
        6: {  # Summer - Semester 6
            "required": [],
            "electives": []  # Optional summer - always empty
        },
        7: {  # Fall - Semester 7
            "required": ["CDA 4205", "COT 4400"],
            "electives": [("Gen-Ed USF Social Sciences (UGES)", "Gen Ed Social"),
                         ("Major Elective - Software", "Software Elective"),
                         ("Major Elective - Software", "Software Elective"),
                         ("Major Elective - Technical", "Technical Elective")]
        },
        8: {  # Spring - Semester 8
            "required": ["CDA 4205L", "EGN 2440", "EGN 4450"],
            "electives": [("AMH/POS (SCIV/SGES)", "Gen Ed Social"),
                         ("Natural Science Elective (no lab)", "Science Elective"),
                         ("Gen-Ed USF Humanities (UGEH)", "Gen Ed Humanities"),
                         ("Major Elective - Software", "Software Elective")]
        },
        9: {  # Summer - Semester 9
            "required": [],
            "electives": []  # Optional summer - always empty
        },
        10: {  # Fall - Semester 10
            "required": ["CNT 4419", "CEN 4020", "CIS 4250"],
            "electives": [("General/Unrestricted Elective", "General Elective"),
                         ("General/Unrestricted Elective", "General Elective")]
        },
        11: {  # Spring - Semester 11
            "required": ["COP 4600"],
            "electives": [("General/Unrestricted Elective", "General Elective"),
                         ("Major Elective - Theory", "Theory Elective"),
                         ("Major Elective - Technical", "Technical Elective"),
                         ("Major Elective - Technical", "Technical Elective")]
        }
    }
    
    study_plan = {}
    completed = set()
    
    # Generate all 11 semesters
    for sem_num in range(1, 12):
        template_sem = base_template.get(sem_num, {"required": [], "electives": []})
        
        semester_courses = []
        
        # Add required courses
        for course_code in template_sem["required"]:
            if course_code in course_catalog and course_code not in completed:
                semester_courses.append(course_code)
                completed.add(course_code)
        
        # Add electives
        for elective_desc, category in template_sem["electives"]:
            # Check if we should exclude labs (look for "no lab" in description)
            exclude_labs = "no lab" in elective_desc.lower()
            elective = get_elective_from_category(course_catalog, category, completed, exclude_labs)
            if elective:
                semester_courses.append(elective)
                completed.add(elective)
        
        # ✅ Always add every semester 1-11 (empty summers included)
        study_plan[str(sem_num)] = semester_courses
    
    return study_plan

def generate_student(student_id, admission_term, course_catalog):
    """
    Generate a synthetic student profile with SAT-based ability & USF study plan.
    """
    
    # 🎯 SAT-driven ability
    sat_score = random.randint(900, 1450)
    academic_ability, predicted_gpa = sat_to_ability_and_gpa(sat_score)
    dropout_chance = round(random.uniform(0.05, 0.2), 2)
    
    # Generate study plan following USF template
    study_plan = generate_study_plan_from_template(course_catalog, admission_term)
    
    return {
        "id": student_id,
        "sat_score": sat_score,
        "predicted_gpa": predicted_gpa,
        "academic_ability": academic_ability,
        "dropout_chance": dropout_chance,
        "admission_term": admission_term,
        "start_term": admission_term,
        "started_in_fall": (admission_term == "Fall"),
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
    
    for term in terms:
        for _ in range(num_per_term):
            students.append(generate_student(student_id, term, course_catalog))
            student_id += 1
    
    return students

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    
    with open("data/course_catalog.json", "r") as f:
        course_catalog = json.load(f)
    
    synthetic_students = generate_students(course_catalog, num_per_term=1000)
    
    with open("data/synthetic_students.json", "w") as f:
        json.dump(synthetic_students, f, indent=2)
    
    print(f"✅ Generated {len(synthetic_students)} synthetic students")
    print(f"   Following USF CS 4-Year Plan structure")
    print(f"   Saved to data/synthetic_students.json")