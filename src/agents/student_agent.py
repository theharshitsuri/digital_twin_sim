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
        self.predicted_gpa = profile.get("predicted_gpa", 2.5)  # SAT-driven predictor
        self.dropout_chance = profile["dropout_chance"]
        self.study_plan = profile["study_plan"]
        self.admission_term = profile.get("admission_term", "Fall")

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
        self.low_gpa_streak = 0  # for probation
        self.graduation_semester = None
        
        # 🆕 Track blocked courses (for analysis)
        self.blocked_courses = []
        
        # 🆕 Build course-to-typical-term mapping for smart retakes
        self.course_typical_term = self._build_course_term_mapping()

    def check_prerequisites(self, course_code):
        """
        Check if student has completed all prerequisites for a course.
        Returns True if eligible to enroll, False otherwise.
        """
        course_info = self.course_catalog.get(course_code, {})
        prerequisites = course_info.get("prerequisites", [])
        
        # Handle courses with multiple prerequisites (must complete ALL)
        if isinstance(prerequisites, list):
            return all(prereq in self.completed_courses for prereq in prerequisites)
        else:
            # Single prerequisite (shouldn't happen with our catalog, but safe)
            return prerequisites in self.completed_courses if prerequisites else True

    def _build_course_term_mapping(self):
        """
        Build a mapping of which term each course is typically offered in
        based on the student's study plan.
        Returns dict: {course_code: term} where term is "Fall", "Spring", or "Summer"
        """
        course_to_term = {}
        term_cycle = ["Fall", "Spring", "Summer"]
        
        # Adjust based on admission term
        term_offset = {"Fall": 0, "Spring": 1, "Summer": 2}
        offset = term_offset.get(self.admission_term, 0)
        
        for sem_str, courses in self.study_plan.items():
            sem_num = int(sem_str)
            # Calculate which term this semester represents
            term_index = (sem_num - 1 + offset) % 3
            term = term_cycle[term_index]
            
            for course in courses:
                if course not in course_to_term:  # First occurrence
                    course_to_term[course] = term
        
        return course_to_term
    
    def should_retry_course(self, course_code):
        """
        Determine if a failed course should be retried this semester based on term matching.
        Returns True if current model term matches the course's typical term, or if unknown.
        """
        typical_term = self.course_typical_term.get(course_code)
        
        # If we don't know the typical term, allow retry anytime
        if typical_term is None:
            return True
        
        # Check if current term matches
        current_term = self.model.current_term
        return current_term == typical_term

    def step(self):
        """Advance one semester for this student."""
        if self.graduated or self.dropped_out:
            return

        # --- Dropout Logic ---
        # Early attrition (low ability + early terms)
        if 2 <= self.semester_num <= 4 and self.academic_ability < 0.65:
            if random.random() < 0.15:
                self.dropped_out = True
                return

        # Academic probation rule
        if self.semester_num > 3 and self.gpa < 2.0:
            self.low_gpa_streak += 1
            if self.low_gpa_streak >= 2:
                self.dropped_out = True
                return
        else:
            self.low_gpa_streak = 0

        # Stagnation rule (too few credits after 4 semesters)
        if self.semester_num == 5 and self.credits_completed < 12:
            self.dropped_out = True
            return

        # Random late attrition
        if self.semester_num >= 6 and random.random() < 0.02:
            self.dropped_out = True
            return

        # --- Course Enrollment with Prerequisite Checking ---
        planned_courses = self.study_plan.get(str(self.semester_num), [])
        
        # 🆕 Add repeat courses ONLY if term matches (smarter scheduling)
        for repeat in list(self.repeat_courses):
            if repeat not in planned_courses and repeat not in self.completed_courses:
                if self.should_retry_course(repeat):
                    planned_courses.append(repeat)
        
        # 🆕 Filter courses by prerequisite eligibility
        enrollable_courses = []
        for course_code in planned_courses:
            # Skip if already completed
            if course_code in self.completed_courses:
                continue
            
            # 🆕 Check prerequisites
            if self.check_prerequisites(course_code):
                enrollable_courses.append(course_code)
            else:
                # Track blocked courses for analysis
                missing_prereqs = [
                    p for p in self.course_catalog.get(course_code, {}).get("prerequisites", [])
                    if p not in self.completed_courses
                ]
                self.blocked_courses.append({
                    'semester': self.semester_num,
                    'term': self.model.current_term,
                    'course': course_code,
                    'missing_prereqs': missing_prereqs
                })

        # Simulate each enrollable course
        for course_code in enrollable_courses:
            grade = self.assign_grade()
            self.transcript[course_code] = grade

            if grade == "F":
                if course_code not in self.repeat_courses:
                    self.repeat_courses.append(course_code)
            else:
                self.completed_courses.add(course_code)
                credits = self.course_catalog.get(course_code, {}).get("credits", 3)
                self.credits_completed += credits
                if course_code in self.repeat_courses:
                    self.repeat_courses.remove(course_code)

        # Update GPA
        self.update_gpa()

        # Graduation check
        if self.credits_completed >= self.model.required_credits and all(
            c in self.completed_courses for c in self.core_courses
        ):
            self.graduated = True
            self.dropped_out = False
            if self.graduation_semester is None:
                self.graduation_semester = self.semester_num

        self.semester_num += 1

    def assign_grade(self):
        """Assign grade influenced by predicted GPA from SAT."""
        grades = ["A", "B", "C", "D", "F"]
        base = self.predicted_gpa  # range ~1.5–4.0

        # Probability weights shaped around predicted GPA
        weights = [
            max(0.1, (base - 2.0) * 2.0),   # A
            max(0.1, (base - 1.5) * 1.8),   # B
            max(0.1, 3.0 - abs(base - 2.5)),# C
            max(0.1, (2.5 - base) * 1.5),   # D
            max(0.1, (2.0 - base) * 2.0)    # F
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