"""
import random
from mesa import Agent

class StudentAgent(Agent):
    def __init__(self, unique_id, model, profile):
        super().__init__(unique_id, model)
        self.unique_id = unique_id
        self.model = model

        # Load from profile (synthetic JSON record)
        self.academic_ability = profile["academic_ability"]
        self.dropout_chance = profile["dropout_chance"]
        self.admission_term = profile["admission_term"]
        self.study_plan = profile.get("study_plan", {})

        # Start state
        self.credits_completed = profile.get("credits_completed", 0)
        self.graduated = profile.get("graduated", False)
        self.drop_out = profile.get("dropped_out", False)
        self.transcript = profile.get("transcript", {})
        self.completed_courses = profile.get("completed_courses", [])
        self.current_courses = profile.get("current_courses", [])
        self.repeat_courses = profile.get("repeat_courses", [])
        self.gpa = profile.get("gpa", 0.0)
        self.semesters_enrolled = 0
        self.graduation_semester_num = -1

    def step(self):
        
        if self.graduated or self.drop_out:
            return

        self.semesters_enrolled += 1
        self.select_courses()
        self.attempt_courses()
        self.calculate_gpa()
        self.check_graduation()
        self.check_dropout()

    def select_courses(self):
        
        planned_courses = []

        if self.repeat_courses:
            planned_courses.extend(self.repeat_courses)

        if str(self.semesters_enrolled) in self.study_plan:
            planned_courses.extend(self.study_plan[str(self.semesters_enrolled)])

        # Remove duplicates + already completed
        planned_courses = list(set(planned_courses) - set(self.completed_courses))

        valid_courses = []
        current_term = self.get_current_term()

        for course_code in planned_courses:
            course_info = self.model.course_catalog.get(course_code)
            if not course_info:
                continue

            # Check prerequisites
            prereqs_met = all(p in self.completed_courses for p in course_info.get("prerequisites", []))

            # Check course availability
            term_ok = current_term in course_info.get("terms_offered", [])

            if prereqs_met and term_ok:
                valid_courses.append(course_code)

                # Add co-reqs
                for coreq in course_info.get("corequisites", []):
                    if coreq not in valid_courses and coreq not in self.completed_courses:
                        valid_courses.append(coreq)

        self.current_courses = valid_courses


    def get_current_term(self):
        
        terms = ["Fall", "Spring", "Summer"]
        return terms[self.semesters_enrolled % 3]


    def attempt_courses(self):
        
        if self.semesters_enrolled not in self.transcript:
            self.transcript[self.semesters_enrolled] = {}

        for course_code in self.current_courses:
            course_info = self.model.course_catalog.get(course_code, {})
            credits = course_info.get("credits", 3)  # fallback = 3 if missing

            passed = random.random() < self.academic_ability
            if passed:
                grade = "A"
                self.completed_courses.append(course_code)
                self.credits_completed += credits
                if course_code in self.repeat_courses:
                    self.repeat_courses.remove(course_code)
            else:
                grade = "F"
                if course_code not in self.repeat_courses:
                    self.repeat_courses.append(course_code)

            # record in transcript
            self.transcript[self.semesters_enrolled][course_code] = {
                "grade": grade,
                "credit": credits
            }

        self.current_courses = []


    def calculate_gpa(self):
        
        grade_points = {"A": 4.0, "B": 3.0, "C": 2.0, "D": 1.0, "F": 0.0}
        best_grades = {}

        for semester, courses in self.transcript.items():
            for course_code, data in courses.items():
                grade = data["grade"]
                credit = data["credit"]

                if course_code not in best_grades or grade_points[grade] > grade_points[best_grades[course_code][0]]:
                    best_grades[course_code] = (grade, credit)

        total_quality_points = sum(grade_points[g] * c for g, c in best_grades.values())
        total_credits = sum(c for _, c in best_grades.values())

        self.gpa = total_quality_points / total_credits if total_credits > 0 else 0.0

    def check_graduation(self):
        
        if self.credits_completed >= self.model.required_credits:
            self.graduated = True
            self.graduation_semester_num = self.semesters_enrolled

    def check_dropout(self):
        
        if self.graduated or self.drop_out:
            return

        dropout_prob = self.dropout_chance
        if self.gpa < 2.0:
            dropout_prob += 0.1

        if random.random() < dropout_prob:
            self.drop_out = True
"""

import random
from mesa import Agent

class StudentAgent(Agent):
    def __init__(self, unique_id, model, profile, course_catalog, core_courses):
        super().__init__(unique_id, model)
        # Load profile from generator
        self.profile = profile
        self.course_catalog = course_catalog
        self.core_courses = core_courses

        # Convenience attributes
        self.academic_ability = profile["academic_ability"]
        self.dropout_chance = profile["dropout_chance"]
        self.study_plan = profile["study_plan"]

        # Progress
        self.credits_completed = profile.get("credits_completed", 0)
        self.completed_courses = set(profile.get("completed_courses", []))
        self.transcript = profile.get("transcript", {})
        self.repeat_courses = profile.get("repeat_courses", [])
        self.gpa = profile.get("gpa", 0.0)

        # Status flags
        self.graduated = profile.get("graduated", False)
        self.dropped_out = profile.get("dropped_out", False)

        # Semester counters
        self.semester_num = 1
        self.low_gpa_streak = 0  # for academic probation
        self.graduation_semester = None  # NEW

    def step(self):
        """Advance one semester for this student."""
        if self.graduated or self.dropped_out:
            return

        # --- Dropout Logic ---
        # Early attrition (low ability, first 4 semesters)
        if 2 <= self.semester_num <= 4 and self.academic_ability < 0.65:
            if random.random() < 0.15:  # 15% chance
                self.dropped_out = True
                return

        # Academic probation rule (low GPA for 2+ consecutive semesters)
        if self.semester_num > 3 and self.gpa < 2.0:
            self.low_gpa_streak += 1
            if self.low_gpa_streak >= 2:
                self.dropped_out = True
                return
        else:
            self.low_gpa_streak = 0

        # Stagnation rule (not enough credits after 4 semesters)
        if self.semester_num == 5 and self.credits_completed < 12:
            self.dropped_out = True
            return

        # Random late attrition
        if self.semester_num >= 6 and random.random() < 0.02:  # 2% chance
            self.dropped_out = True
            return

        # --- Course Enrollment ---
        semester_courses = self.study_plan.get(str(self.semester_num), [])

        # Add repeat courses if not already passed
        for repeat in list(self.repeat_courses):
            if repeat not in semester_courses and repeat not in self.completed_courses:
                semester_courses.append(repeat)

        # Simulate each course
        for course_code in semester_courses:
            if course_code in self.completed_courses:
                continue  # already passed

            grade = self.assign_grade(self.academic_ability)
            self.transcript[course_code] = grade

            if grade == "F":
                if course_code not in self.repeat_courses:
                    self.repeat_courses.append(course_code)
            else:
                self.completed_courses.add(course_code)
                self.credits_completed += self.course_catalog.get(course_code, {}).get("credits", 3)
                if course_code in self.repeat_courses:
                    self.repeat_courses.remove(course_code)

        # Update GPA
        self.update_gpa()

        # Check graduation
        if self.credits_completed >= self.model.required_credits and all(
            c in self.completed_courses for c in self.core_courses
        ):
            self.graduated = True
            self.dropped_out = False
            if self.graduation_semester is None:  # record once
                self.graduation_semester = self.semester_num

        # Move to next semester (allow up to 14)
        self.semester_num += 1

    def assign_grade(self, ability):
        """Assign grade influenced by academic ability."""
        grades = ["A", "B", "C", "D", "F"]
        weights = [
            ability * 4,        # A
            ability * 2.5,      # B
            (1 - ability) * 2,  # C
            (1 - ability) * 1.5,# D
            (1 - ability) * 4   # F
        ]
        return random.choices(grades, weights=weights, k=1)[0]

    def update_gpa(self):
        """Recalculate GPA from transcript."""
        mapping = {"A": 4.0, "B": 3.0, "C": 2.0, "D": 1.0, "F": 0.0}
        if not self.transcript:
            self.gpa = 0.0
            return
        points = [mapping[g] for g in self.transcript.values()]
        self.gpa = round(sum(points) / len(points), 2)
