from mesa import Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
from src.agents.student_agent import StudentAgent

class UniversityModel(Model):
    def __init__(self, students_data, course_catalog, required_credits=120):
        super().__init__()
        self.course_catalog = course_catalog
        self.required_credits = required_credits
        self.schedule = RandomActivation(self)
        self.semester_count = 0
        self.running = True
        
        # 🆕 Track current academic term
        self.current_term = "Fall"  # Starting term
        self.term_cycle = ["Fall", "Spring", "Summer"]
        
        # Identify CS Core courses (must complete to graduate)
        self.core_courses = [
            c for c, info in course_catalog.items()
            if info.get("category") == "CS Core"
        ]
        
        # Create student agents
        for i, profile in enumerate(students_data):
            student = StudentAgent(
                unique_id=i,
                model=self,
                profile=profile,
                course_catalog=self.course_catalog,
                core_courses=self.core_courses
            )
            self.schedule.add(student)
        
        # Collect stats
        self.datacollector = DataCollector(
            model_reporters={
                "Semester": lambda m: m.semester_count,
                "Term": lambda m: m.current_term,
                "Graduated": self.count_graduated,
                "DroppedOut": self.count_dropped_out,
                "Enrolled": self.count_enrolled,
                "AvgGPA": self.avg_gpa,
                "TotalBlocked": self.count_total_blocked  # 🆕 Track bottlenecks
            }
        )
    
    def step(self):
        """Advance simulation by one semester."""
        self.semester_count += 1
        
        # 🆕 Update current term (Fall → Spring → Summer → Fall...)
        term_index = (self.semester_count - 1) % 3
        self.current_term = self.term_cycle[term_index]
        
        self.datacollector.collect(self)
        self.schedule.step()
        
        # Stop if no students left
        if self.count_enrolled() == 0:
            self.running = False
    
    # --- Metrics ---
    def count_graduated(self):
        return sum(1 for s in self.schedule.agents if s.graduated)
    
    def count_dropped_out(self):
        return sum(1 for s in self.schedule.agents if s.dropped_out)
    
    def count_enrolled(self):
        return sum(1 for s in self.schedule.agents if not s.graduated and not s.dropped_out)
    
    def avg_gpa(self):
        gpas = [s.gpa for s in self.schedule.agents if s.gpa > 0]
        return round(sum(gpas) / len(gpas), 2) if gpas else 0.0
    
    def count_total_blocked(self):
        """🆕 Count total number of course blockages this semester"""
        return sum(
            len([b for b in s.blocked_courses if b['semester'] == self.semester_count])
            for s in self.schedule.agents
            if not s.graduated and not s.dropped_out
        )