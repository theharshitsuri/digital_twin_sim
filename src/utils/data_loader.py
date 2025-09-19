import json
import matplotlib.pyplot as plt
from src.model.university_model import UniversityModel

if __name__ == "__main__":
    # Load synthetic students (JSON file you generated earlier)
    with open("data/synthetic_students.json", "r") as f:
        students_data = json.load(f)

    # Load course catalog (JSON file we created)
    with open("data/course_catalog.json", "r") as f:
        course_catalog = json.load(f)

    # Initialize model with students + course catalog
    bscs_model = UniversityModel(
        students_data=students_data,
        course_catalog=course_catalog,   # <--- added
        required_credits=120
    )

    # Run for up to 12 semesters (6 years)
    for _ in range(12):
        if not bscs_model.running:
            break
        bscs_model.step()

    # Collect results
    results = bscs_model.datacollector.get_model_vars_dataframe()
    results.index.name = "Semester" 
    results.to_csv("data/results.csv")

    print("Simulation finished ✅")
    print(results.tail(1))  # Final snapshot

    # Plot results
    results.plot()
    plt.title("Student Progression Over Time")
    plt.xlabel("Semester")
    plt.ylabel("Number of Students")
    plt.show()
