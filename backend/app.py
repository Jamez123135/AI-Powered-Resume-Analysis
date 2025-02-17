from flask import Flask, request, jsonify, render_template, redirect
import os
import fitz
import uuid
from werkzeug.utils import secure_filename
from pdfminer.high_level import extract_text as pdfminer_extract
from resume_analysis import analyze_resume, extract_job_skills, compare_skills, analyze_match
from job import parse_job_description
from PyPDF2 import PdfReader
import re

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def read_pdf(file):
    try:
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        if not text:
            raise ValueError("No extractable text found in the PDF")
        print("Extracted Text:")  # Debugging: print extracted text
        print(text[:500])  # Print only the first 500 characters for review
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""


def extract_experience(text):
    # Define keywords and possible section headers for experience
    experience_keywords = [
        r"\b(experience|work history|employment|professional experience)\b",  # Regex for keywords
        r"\b(work experience|career summary)\b",  # Additional variations
    ]

    # Split text into lines
    lines = text.split("\n")
    print("Lines after splitting text:")
    print(lines[:10])  # Print the first 10 lines for review

    experience_section = []

    capture = False
    for line in lines:
        line_lower = line.lower().strip()

        # Debugging: check the line
        print(f"Checking line: {line_lower}")

        # Check for any experience-related keywords or section headers
        if any(re.search(keyword, line_lower) for keyword in experience_keywords):
            capture = True
            continue  # Skip the keyword/section header itself

        # Stop capturing if we reach other sections like education, skills, etc.
        if capture and any(line_lower.startswith(section) for section in ["education", "skills", "projects"]):
            break

        if capture:
            experience_section.append(line)

    print("Extracted experience section:")
    print("\n".join(experience_section))  # Print the experience section

    return "\n".join(experience_section).strip()

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/new", methods=["GET", "POST"])
def new():
    return render_template("new.html")

@app.route("/experience")
def experience():
    return render_template("new.html", experience=experience)


@app.route("/jobseeker")
def jobseeker():
    return render_template("job_seeker.html")


@app.route("/recruiter")
def recruiter():
    return render_template("recruiter.html")

# Endpoint for Job Seeker Analysis
@app.route("/compare", methods=["POST", "GET"])
def compare_resume_job():
    resume_file = request.files["resume"]
    job_text = request.form.get("job_description", "")

    if "resume" not in request.files:
        return jsonify({"error": "No resume file"}), 400

    if not (resume_file and resume_file.filename):
        return jsonify({"error": "Empty resume file"}), 400
    if not job_text.strip():
        return jsonify({"error": "Empty job description"}), 400

    # Process the resume file.
    resume_analysis = process_resume(resume_file)
    if "error" in resume_analysis:
        return jsonify(resume_analysis), 500

    # Parse the job description to extract required skills, experience, and education.
    job_data = parse_job_description(job_text)

    # ✅ Ensure `required_skills` exists and is a list.
    if "required_skills" not in job_data or not isinstance(job_data["required_skills"], list):
        job_data["required_skills"] = []  # Prevents undefined errors

    # Compare skills (for a basic overview).
    skill_comparison = compare_skills(resume_analysis["skills"], job_data["required_skills"])

    # Get the composite match result using the new matching logic.
    match_result = analyze_match(resume_analysis, job_data)

    response_data = {
        "message": "Comparison successful",
        "skill_comparison": skill_comparison,
        "match_result": match_result,
        "analysis": resume_analysis,
        "job_data": job_data
    }

      # Debugging Output

    return jsonify(response_data), 200

# Endpoint for Recruiter (Multiple Resume Analysis)
@app.route("/compare-multiple", methods=["POST"])
def compare_multiple_resumes():
    resumes = request.files.getlist("resumes")
    job_text = request.form.get("job_description", "")

    if not resumes or all(r.filename == '' for r in resumes):
        return jsonify({"error": "No resume files uploaded"}), 400
    if not job_text.strip():
        return jsonify({"error": "Empty job description"}), 400

    job_data = parse_job_description(job_text)
    results = []
    for resume in resumes:
        try:
            resume_analysis = process_resume(resume)

            if "error" in resume_analysis:
                results.append({
                    "filename": resume.filename,
                    "error": resume_analysis["error"]
                })
                continue

            skill_comparison = compare_skills(resume_analysis["skills"], job_data.get("required_skills", []))
            match_result = analyze_match(resume_analysis, job_data)
            results.append({
                "filename": resume.filename,
                "skill_comparison": skill_comparison,
                "match_result": match_result,
                "analysis": resume_analysis
            })
        except Exception as e:
            results.append({
                "filename": resume.filename,
                "error": f"Failed to process resume: {str(e)}"
            })

    # Sort the results in descending order based on the 'final_match' value after stripping the '%' symbol.
    results = sorted(
        results,
        key=lambda r: float(r.get("match_result", {}).get("final_match", "0").replace('%', '').strip()),
        reverse=True
    )

    return jsonify({
        "message": "Comparison completed",
        "results": results,
        "job_data": job_data
    }), 200


def process_resume(file):
    try:
        # Generate a unique filename to prevent overwrites
        unique_id = uuid.uuid4().hex
        original_name = secure_filename(file.filename)
        filename = f"{unique_id}_{original_name}"
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)
        # Rest of the code...

        raw_text = parse_pdf(filepath)
        if raw_text.startswith("Error:"):
            return {"error": raw_text}

        return analyze_resume(raw_text)

    except Exception as e:
        return {"error": f"Processing error: {str(e)}"}


def parse_pdf(filepath):
    """Extract text from PDF using PyMuPDF, fallback to pdfminer."""
    text = ""
    try:
        with fitz.open(filepath) as doc:
            text = "".join(page.get_text() for page in doc)
            if text.strip():
                return text.strip()
    except Exception:
        pass

    try:
        return pdfminer_extract(filepath).strip()
    except Exception as e:
        return f"Error: Failed to extract text - {str(e)}"


if __name__ == "__main__":
    app.run(debug=True)
