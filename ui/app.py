import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# --- Page Config ---
st.set_page_config(page_title="Digital Twin Simulation", layout="wide")
st.title("Digital Twin Simulation Dashboard")

# --- Load Simulation Results ---
try:
    results = pd.read_csv("data/results.csv")
except FileNotFoundError:
    st.error("No results.csv found. Run `python -m src.simulation_runner` first.")
    st.stop()

# --- Summary Stats ---
st.subheader("Final Snapshot")
final_row = results.tail(1).to_dict("records")[0]
col1, col2, col3 = st.columns(3)
col1.metric("Graduated", final_row["Graduated"])
col2.metric("Dropped Out", final_row["DroppedOut"])
col3.metric("Still Enrolled", final_row["Enrolled"])

# --- Show Table ---
st.subheader("Simulation Results by Semester")
st.dataframe(results)

# --- Plot Results ---
st.subheader("Graduation vs Dropout vs Enrollment")
fig, ax = plt.subplots(figsize=(8, 5))
results.set_index("Semester")[["Graduated", "DroppedOut", "Enrolled"]].plot(ax=ax, marker="o")
ax.set_xlabel("Semester")
ax.set_ylabel("Number of Students")
ax.set_title("Student Progression Over Time")
st.pyplot(fig)

# --- Extra Option: Download Results ---
st.subheader("Export Results")
st.download_button(
    label="Download results as CSV",
    data=results.to_csv(index=False).encode("utf-8"),
    file_name="simulation_results.csv",
    mime="text/csv",
)
