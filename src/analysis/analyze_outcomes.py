import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

def analyze_student_outcomes(file_path="data/student_outcomes.csv"):
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return

    df = pd.read_csv(file_path)
    print("✅ Loaded outcomes:", df.shape, "records")

    # --- Summary statistics ---
    print("\n--- Summary ---")
    print(df.describe())

    grad_count = df["graduated"].sum()
    dropout_count = df["dropped_out"].sum()
    enrolled_count = len(df) - grad_count - dropout_count

    print(f"\nGraduated: {grad_count}")
    print(f"Dropped Out: {dropout_count}")
    print(f"Still Enrolled: {enrolled_count}")

    # --- Histograms ---
    sns.set_style("whitegrid")

    # Credits distribution
    plt.figure(figsize=(8,5))
    sns.histplot(df["credits_completed"], bins=20, kde=False)
    plt.title("Distribution of Credits Completed")
    plt.xlabel("Credits Completed")
    plt.ylabel("Number of Students")
    plt.savefig("data/credits_distribution.png")
    plt.show()

    # GPA distribution
    plt.figure(figsize=(8,5))
    sns.histplot(df["gpa"], bins=20, kde=True)
    plt.title("Distribution of GPA")
    plt.xlabel("GPA")
    plt.ylabel("Number of Students")
    plt.savefig("data/gpa_distribution.png")
    plt.show()

    # Outcomes breakdown
    plt.figure(figsize=(6,6))
    labels = ["Graduated", "Dropped Out", "Still Enrolled"]
    sizes = [grad_count, dropout_count, enrolled_count]
    plt.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=140)
    plt.title("Final Outcomes")
    plt.savefig("data/outcome_pie.png")
    plt.show()

    # GPA vs Credits
    plt.figure(figsize=(8,5))
    sns.scatterplot(data=df, x="credits_completed", y="gpa", hue="graduated")
    plt.title("GPA vs Credits Completed")
    plt.savefig("data/gpa_vs_credits.png")
    plt.show()

if __name__ == "__main__":
    analyze_student_outcomes()
