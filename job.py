from flask import Flask, request, jsonify
import spacy
import re
from spacy.matcher import PhraseMatcher
from data_base import SKILLS_DB

app = Flask(__name__)

# Load the NLP model
nlp = spacy.load("en_core_web_sm")

# ===================== SKILL MAPPING & MATCHER SETUP =====================
# Build a consistent skill mapping: lower-case alias -> canonical skill
SKILL_MAPPING = {
    alias.lower(): skill
    for skill, aliases in SKILLS_DB.items()
    for alias in aliases
}
# Ensure the canonical skill is also mapped.
for skill in SKILLS_DB.keys():
    SKILL_MAPPING[skill.lower()] = skill

# Build PhraseMatcher using lower-case patterns.
matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
patterns = [nlp.make_doc(alias.lower()) for aliases in SKILLS_DB.values() for alias in aliases]
matcher.add("SKILLS", None, *patterns)


# ===================== JOB DESCRIPTION PARSER =====================
def parse_job_description(job_text: str) -> dict:
    """
    Parse a job description to extract required skills, years of experience,
    education requirements, and calculate a skills match percentage.

    :param job_text: The job description text.
    :return: A dictionary containing parsed job data.
    """
    parsed_job = {
        "required_skills": [],
        "years_experience": None,
        "education": None,
        "skills_match_percentage": 0
    }

    # Convert job text to lower-case for uniform processing.
    job_text_lower = job_text.lower()
    doc = nlp(job_text_lower)
    skills_found = set()

    # 1. Phrase-based matching using PhraseMatcher.
    matches = matcher(doc)
    for match_id, start, end in matches:
        span = doc[start:end]
        canonical = SKILL_MAPPING.get(span.text)
        if canonical:
            skills_found.add(canonical)

    # 2. Lemmatization-based matching.
    for token in doc:
        canonical = SKILL_MAPPING.get(token.lemma_.lower())
        if canonical:
            skills_found.add(canonical)

    # 3. Handle compound nouns (e.g., "machine learning").
    for chunk in doc.noun_chunks:
        canonical = SKILL_MAPPING.get(chunk.text.lower())
        if canonical:
            skills_found.add(canonical)

    # Calculate skills match percentage.
    total_mentions = sum(1 for token in doc if token.text in SKILL_MAPPING)
    matched_skills = len(skills_found)
    if total_mentions > 0:
        parsed_job["skills_match_percentage"] = min((matched_skills / total_mentions) * 100, 100)

    parsed_job["required_skills"] = sorted(skills_found)

    # Extract years of experience.
    experience_pattern = r'(\d+[\+\.]?\d*)\s+(years?|yrs?)(?:\s+of)?\s+(experience|exp|industry)'
    experience_match = re.search(experience_pattern, job_text, re.IGNORECASE)
    if experience_match:
        years = experience_match.group(1)
        parsed_job["years_experience"] = f"{years} years"

    # Extract education requirement.
    education_pattern = r'\b(PhD|Doctorate|M\.?S\.?|M\.?Eng|M\.?A\.?|Master|B\.?S\.?|B\.?A\.?|B\.?Eng|Bachelor)\b'
    education_match = re.search(education_pattern, job_text, re.IGNORECASE)
    if education_match:
        degree = education_match.group(1).title()
        # Normalize degree names.
        degree = re.sub(r'^M\.?S\.?$', 'Master', degree)
        degree = re.sub(r'^B\.?S\.?$', 'Bachelor', degree)
        parsed_job["education"] = degree

    return parsed_job


# ===================== FLASK ROUTE FOR JOB DESCRIPTION =====================
@app.route('/upload_job_description', methods=['POST'])
def upload_job_description():
    """
    Endpoint to process a job description.
    Accepts JSON or form-data with a 'job_description' key and returns the parsed job data.
    """
    try:
        # Support both JSON and form-data input.
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form

        job_text = data.get("job_description")
        if not job_text:
            return jsonify({"error": "No job_description provided"}), 400

        parsed_job = parse_job_description(job_text)
        return jsonify({
            "message": "Job description processed successfully",
            "job_data": parsed_job
        }), 200

    except Exception as e:
        # In production, consider logging the exception details.
        return jsonify({"error": f"Invalid request format: {str(e)}"}), 400


# Run the Flask app.
if __name__ == "__main__":
    app.run(debug=True)
