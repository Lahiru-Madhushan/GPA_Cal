import io
import os
import re
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

import pandas as pd
import pdfplumber
import streamlit as st


# -----------------------------
# Parsing and GPA calculation
# -----------------------------

MODULE_PATTERN = re.compile(r"(IT\d{3,4})", re.IGNORECASE)
GRADE_PATTERN = re.compile(r"^[A-F][+-]?$|^[0-9]{1,3}(?:\.[0-9]+)?$", re.IGNORECASE)
REG_PATTERN = re.compile(r"^IT\w*", re.IGNORECASE)

# Grade -> grade point mapping
GP_MAP: Dict[str, float] = {
    "A+": 4.0,
    "A": 4.0,
    "A-": 3.7,
    "B+": 3.3,
    "B": 3.0,
    "B-": 2.7,
    "C+": 2.3,
    "C": 2.0,
    "C-": 1.7,
    "D+": 1.3,
    "D": 1.0,
    "E": 0.0,
    "F": 0.0,
}

# Default module credits (can be adjusted here)
CREDITS: Dict[str, int] = {

    # ------------------------
    # Year 1 – Common IT
    # ------------------------
    "IT1010": 4,  # Introduction to Programming
    "IT1020": 4,  # Introduction to Computer Systems
    "IT1030": 4,  # Mathematics for Computing
    "IT1040": 3,  # Communication Skills
    "IT1050": 2,  # Object Oriented Concepts
    "IT1060": 3,  # Software Process Modeling
    "IT1080": 3,  # English for Academic Purposes
    "IT1090": 4,  # Information Systems and Data Modeling
    "IT1100": 4,  # Internet and Web Technologies

    # ------------------------
    # Year 2 – Core IT
    # ------------------------
    "IT2020": 4,  # Software Engineering
    "IT2030": 4,  # Object Oriented Programming
    "IT2040": 4,  # Database Management Systems
    "IT2050": 4,  # Computer Networks
    "IT2060": 4,  # Operating Systems & System Administration
    "IT2070": 4,  # Data Structures and Algorithms
    "IT2080": 4,  # IT Project
    "IT2090": 2,  # Professional Skills
    "IT2100": 1,  # Employability Skills Development – Seminar
    "IT2110": 3,  # Probability and Statistics

    # ------------------------
    # Year 3 – IT / SE
    # ------------------------
    "IT3010": 4,  # Network Design and Management
    "IT3020": 4,  # Database Systems
    "IT3030": 4,  # Programming Applications & Frameworks
    "IT3040": 4,  # IT Project Management
    "IT3050": 1,  # Employability Skills Development – Seminar (NGPA)
    "IT3060": 4,  # Human Computer Interaction
    "IT3070": 4,  # Information Assurance & Security
    "IT3080": 4,  # Data Science & Analytics
    "IT3090": 3,  # Business Management for IT
    "IT3110": 8,  # Industry Placement

    # ------------------------
    # Year 4 – IT
    # ------------------------
    "IT4010": 16, # Research Project
    "IT4070": 2,  # Preparation for the Professional World
    "IT4020": 4,  # Modern Topics in IT
    "IT4030": 4,  # Internet of Things
    "IT4040": 4,  # Database Administration
    "IT4050": 4,  # Innovation Management & Entrepreneurship
    "IT4060": 4,  # Machine Learning
    "IT4090": 4,  # Cloud Computing
    "IT4100": 4,  # Software Quality Assurance
    "IT4110": 4,  # Computer Systems & Network Administration
    "IT4120": 4,  # Knowledge Management
    "IT4130": 4,  # Image Understanding & Processing

    # ------------------------
    # Software Engineering (SE)
    # ------------------------
    "SE1010": 4,  # Software Engineering
    "SE2010": 4,  # Object Oriented Programming
    "SE2020": 4,  # Web and Mobile Technologies
    "SE3010": 4,  # Software Engineering Process & Quality Management
    "SE3020": 4,  # Distributed Systems
    "SE3030": 4,  # Software Architecture
    "SE3040": 4,  # Application Frameworks
    "SE3050": 3,  # User Experience Engineering
    "SE3060": 4,  # Database Systems
    "SE3070": 4,  # Case Studies in Software Engineering
    "SE3080": 3,  # Software Project Management
    "SE4010": 4,  # Current Trends in Software Engineering
    "SE4020": 4,  # Mobile Application Design & Development
    "SE4030": 4,  # Secure Software Development
    "SE4040": 4,  # Enterprise Application Development
    "SE4050": 4,  # Deep Learning
    "SE4060": 4,  # Parallel Computing

    # ------------------------
    # Information Engineering (IE)
    # ------------------------
    "IE1004": 4,  # Computational Thinking
    "IE1014": 3,  # Engineering Mathematics I
    "IE1024": 3,  # Computer Organization & Architecture
    "IE1034": 3,  # Engineering Mathematics II
    "IE1044": 3,  # Digital Electronics
    "IE2004": 3,  # Computer Networks
    "IE2024": 3,  # Probability and Statistics
    "IE2034": 3,  # Analog Electronics
    "IE2044": 3,  # System Modelling & Prototyping
    "IE2064": 4,  # Advanced Computer Organization & Architecture
    "IE2074": 3,  # Control Theory
    "IE2084": 3,  # Communication Technologies
}


def _extract_module_code_from_name(name: str) -> Optional[str]:
    m = MODULE_PATTERN.search(name)
    return m.group(1).upper() if m else None


def _grade_to_gp(grade: Optional[str]) -> Optional[float]:
    if not isinstance(grade, str):
        return None
    g = grade.strip().upper()
    return GP_MAP.get(g)


def parse_result_pdfs(files: List[Tuple[str, bytes]]) -> pd.DataFrame:
    """
    Parse multiple PDF result sheets into a wide student x module dataframe.

    :param files: list of (filename, bytes) tuples
    :return: DataFrame with columns: Registration No, module codes..., GPA
    """
    student_results: Dict[str, Dict[str, str]] = defaultdict(dict)
    found_modules = set()

    for filename, file_bytes in files:
        module_code = _extract_module_code_from_name(filename)

        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            # Try to find module code in text if not in filename
            if not module_code:
                for page in pdf.pages:
                    txt = page.extract_text() or ""
                    mm = MODULE_PATTERN.search(txt)
                    if mm:
                        module_code = mm.group(1).upper()
                        break

            for page in pdf.pages:
                table = page.extract_table()
                if not table or len(table) <= 1:
                    continue

                for row in table[1:]:
                    if not row:
                        continue

                    # Find registration number in the row
                    reg_no = None
                    for cell in row:
                        if isinstance(cell, str) and REG_PATTERN.match(cell.strip()):
                            reg_no = cell.strip()
                            break
                    if not reg_no:
                        continue

                    # Find grade in the row (from the end)
                    grade = None
                    for cell in reversed(row):
                        if isinstance(cell, str) and cell.strip():
                            val = cell.strip()
                            if GRADE_PATTERN.match(val):
                                grade = val
                                break
                    # Fallback to some common indices
                    if not grade:
                        for idx in (3, 2, 4, 5):
                            if len(row) > idx and isinstance(row[idx], str) and row[idx].strip():
                                cand = row[idx].strip()
                                if GRADE_PATTERN.match(cand):
                                    grade = cand
                                    break

                    mod = module_code if module_code else ""
                    if not mod:
                        continue

                    found_modules.add(mod)
                    student_results[reg_no][mod] = grade

    if not student_results:
        return pd.DataFrame(columns=["Registration No", "GPA"])

    # Build dataframe
    all_modules = sorted(found_modules)
    rows = []
    for reg_no, mods in sorted(student_results.items()):
        row = {"Registration No": str(reg_no).replace(" ", "")}
        for mod in all_modules:
            row[mod] = mods.get(mod)
        rows.append(row)

    df = pd.DataFrame(rows)

    # Compute GPA
    module_cols = [c for c in df.columns if c != "Registration No"]
    gpas: List[Optional[float]] = []

    for _, row in df.iterrows():
        total_points = 0.0
        total_credits = 0.0
        for mod in module_cols:
            grade = row.get(mod)
            gp = _grade_to_gp(grade)
            if gp is not None:
                cr = CREDITS.get(mod, 1)
                total_points += gp * cr
                total_credits += cr

        if total_credits > 0:
            gpas.append(round(total_points / total_credits, 2))
        else:
            gpas.append(None)

    df["GPA"] = gpas

    # Drop students without GPA
    df = df.dropna(subset=["GPA"])

    return df


def add_ranks(df: pd.DataFrame) -> pd.DataFrame:
    """Add rank (1 = best) and percentile columns based on GPA."""
    if "GPA" not in df.columns or df.empty:
        return df

    df = df.copy()
    # Rank: higher GPA = better (rank 1)
    df["Rank"] = df["GPA"].rank(ascending=False, method="min").astype(int)
    df["Total_Students"] = len(df)
    df["Percentile"] = (1 - (df["Rank"] - 1) / (df["Total_Students"])) * 100
    df["Percentile"] = df["Percentile"].round(2)
    return df


# -----------------------------
# Streamlit UI
# -----------------------------

st.set_page_config(page_title="Result GPA Analyzer", layout="wide")

st.title("Student Result GPA Analyzer")
st.markdown(
    "Upload multiple PDF result sheets, compute **GPA** for all students, "
    "and view **per-student GPA, rank, and graphs**."
)

with st.sidebar:
    st.header("1. Upload result PDFs")
    uploaded_files = st.file_uploader(
        "Select one or more PDF result sheets",
        type=["pdf"],
        accept_multiple_files=True,
    )

    st.markdown("---")
    st.header("2. Student lookup")
    reg_input = st.text_input(
        "Enter Registration Number",
        help="Example: IT20XXXX or your registration format",
    )

if not uploaded_files:
    st.info("Upload at least one PDF result sheet to begin.")
    st.stop()

# Convert uploaded files to (name, bytes)
file_payload = [(f.name, f.read()) for f in uploaded_files]

with st.spinner("Processing uploaded PDFs and calculating GPA..."):
    df = parse_result_pdfs(file_payload)
    df = add_ranks(df)

if df.empty:
    st.error("No valid student records or GPAs were parsed from the uploaded PDFs.")
    st.stop()

st.success(f"Processed {len(uploaded_files)} PDF file(s). Found **{len(df)}** students.")

tab_overview, tab_student, tab_table = st.tabs(
    ["📊 GPA Overview", "👤 Student Details", "📋 Full Results Table"]
)

with tab_overview:
    st.subheader("GPA Distribution")
    st.caption("Histogram of GPAs for all students.")
    st.bar_chart(df["GPA"].value_counts().sort_index())

    st.subheader("GPA vs Rank")
    st.caption("Scatter plot of GPA against student rank.")
    st.scatter_chart(df.sort_values("Rank"), x="Rank", y="GPA")

with tab_student:
    st.subheader("Lookup Student by Registration Number")

    if not reg_input:
        st.info("Enter a registration number in the sidebar to see details.")
    else:
        norm_reg = reg_input.replace(" ", "").strip()
        student_row = df[df["Registration No"].str.upper() == norm_reg.upper()]

        if student_row.empty:
            st.error(
                f"No student found with registration number `{norm_reg}`. "
                "Check the value or try another ID."
            )
        else:
            row = student_row.iloc[0]
            st.markdown(
                f"**Registration No:** `{row['Registration No']}`  \n"
                f"**GPA:** `{row['GPA']}`  \n"
                f"**Rank:** `{row['Rank']}` out of `{row['Total_Students']}` students  \n"
                f"**Percentile:** `{row['Percentile']}th`"
            )

            # Highlighted GPA distribution
            st.markdown("#### Student GPA vs Others")
            df_sorted = df.sort_values("GPA", ascending=False).reset_index(drop=True)
            st.line_chart(df_sorted["GPA"])
            st.caption(
                "Line chart of GPA for all students (sorted), "
                "use the rank information above to locate this student."
            )

with tab_table:
    st.subheader("All Students and GPAs")
    st.dataframe(df.reset_index(drop=True))

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download results as CSV",
        data=csv,
        file_name="student_results_gpa.csv",
        mime="text/csv",
    )


