# GPA Calculator (Streamlit)

Streamlit app that parses uploaded result-sheet PDFs, computes student GPA (with ranks and percentiles), and lets you explore results or download them as CSV.

## Prerequisites
- Python 3.10+ (if running locally)
- Docker (optional, for containerized run)

## Local setup
```bash
python -m venv .venv
. .venv/bin/activate    # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```
Open http://localhost:8501.

## Docker
Build and run:
```bash
docker build -t gpa-calculator .
docker run --rm -p 8501:8501 gpa-calculator
```
Then open http://localhost:8501.

## Usage
1) Upload one or more PDF result sheets in the sidebar (see `sampleData/` for examples).
2) The app extracts registration numbers and grades, calculates GPA per student, and ranks them.
3) Browse:
   - GPA overview charts
   - Student lookup by registration number
   - Full results table with CSV download

## Notes
- Grade-to-GPA mapping and default credits are defined in `app.py` (`GP_MAP`, `CREDITS`).
- Parsing relies on patterns for module codes (e.g., `IT2020`) and grades (A-F or numeric). Adjust the regex or mappings in `app.py` if your PDF format differs.

