import re
import logging
from collections import defaultdict
from typing import List, Dict, Any, Set

import spacy
from spacy.matcher import PhraseMatcher
from data_base import SKILLS_DB

# Configure logging (for production, configure appropriately)
logging.basicConfig(level=logging.INFO)

# ===================== INITIAL SETUP =====================
# Load the spaCy model once.
nlp = spacy.load("en_core_web_sm")

# Build a mapping of all skill variations (lowercase) to their canonical name.
SKILL_MAPPING: Dict[str, str] = {
    variation.lower(): canonical
    for canonical, variations in SKILLS_DB.items()
    for variation in variations
}

# Create PhraseMatcher patterns for skills.
SKILL_PATTERNS = [nlp.make_doc(variation) for variants in SKILLS_DB.values() for variation in variants]
SKILL_MATCHER = PhraseMatcher(nlp.vocab, attr="LOWER")
SKILL_MATCHER.add("SKILL", SKILL_PATTERNS)

# ===================== DEGREE & EDUCATION CONSTANTS =====================
# Degree hierarchy: lower index means a higher qualification.
DEGREE_HIERARCHY: List[str] = [
    "PhD", "Doctorate", "MD", "JD", "Master", "MBA", "MSc", "MA",
    "BSc", "BA", "BEng", "Bachelor", "Associate", "Diploma", "Certificate"
]
# Compile a regex pattern to match any degree from the hierarchy (case-insensitive).
DEGREE_PATTERN = re.compile(r'(?i)\b(?:' + '|'.join(DEGREE_HIERARCHY) + r')\b')

# Mapping variations to standard degree names.
DEGREE_MAPPING: Dict[str, str] = {
    'bs': 'Bachelor', 'bsc': 'Bachelor', 'b.a.': 'Bachelor', 'ba': 'Bachelor',
    'ms': 'Master', 'msc': 'Master', 'm.a.': 'Master', 'ma': 'Master',
    'phd': 'PhD', 'doctorate': 'PhD', 'beng': 'Bachelor', 'meng': 'Master'
}

# Skill boost factor and composite threshold.
SKILL_BOOST = 1.1  # 10% boost (previous comment said 30%; please adjust if needed)
COMPOSITE_THRESHOLD = 80.0


# ===================== JOB SKILLS EXTRACTION =====================
def extract_job_skills(job_text: str) -> List[str]:
    """
    Extract skills from a job description using SKILLS_DB.

    :param job_text: The job description text.
    :return: A list of detected skill names.
    """
    job_skills: Set[str] = set()
    # Lowercase the job text for case-insensitive matching.
    doc = nlp(job_text.lower())

    # Match skills token-by-token using the mapping.
    for token in doc:
        if token.text in SKILL_MAPPING:
            job_skills.add(SKILL_MAPPING[token.text])

    # Check for multi-word skills (e.g., "machine learning")
    for skill, variations in SKILLS_DB.items():
        for variation in variations:
            if variation.lower() in job_text.lower():
                job_skills.add(skill)

    # --- AUTOMATIC ENGLISH REQUIREMENT ---
    if "english" in job_text.lower():
        job_skills.add("English")

    return list(job_skills)


# ===================== SKILL COMPARISON =====================
def compare_skills(resume_skills: List[str], job_skills: List[str]) -> Dict[str, Any]:
    """
    Compare resume skills with job skills and calculate match percentages.

    :param resume_skills: List of skills from the resume.
    :param job_skills: List of required job skills.
    :return: Dictionary with match percentage, matched skills, and missing skills.
    """
    resume_set = {skill.lower() for skill in resume_skills}
    job_set = {skill.lower() for skill in job_skills}
    match_percentage = (len(resume_set & job_set) / len(job_set)) * 100 if job_set else 0

    return {
        "match_percentage": f"{match_percentage:.1f}%",
        "matched_skills": sorted(resume_set & job_set),
        "missing_skills": sorted(job_set - resume_set)
    }


# ===================== SECTION EXTRACTION =====================
def extract_sections(text: str) -> Dict[str, List[str]]:
    """
    Extract sections from resume text based on common headers.
    Headers indicating experience are mapped to the key "Experience".

    :param text: Full resume text.
    :return: Dictionary with section names as keys and list of section lines as values.
    """
    experience_headers = [
        'experience', 'work experience', 'employment', 'professional experience',
        'career', 'work history', 'professional background'
    ]
    other_headers = [
        'education', 'skills', 'projects', 'summary', 'academic', 'roles',
        'technical expertise', 'core competencies'
    ]
    project_headers = [
        'projects', 'personal projects', 'extracurricular', 'highlights',
        'notable work', 'achievements', 'projects_highlights'
    ]
    all_headers = experience_headers + project_headers + other_headers

    sections = defaultdict(list)
    current_section = None

    for line in text.split('\n'):
        clean_line = line.strip()
        lower_line = clean_line.lower()
        header_found = False

        # Check if the line starts with any header (and is short enough to be a header)
        for header in all_headers:
            if lower_line.startswith(header) and len(clean_line) < 50:
                if header in experience_headers:
                    current_section = "Experience"
                elif header in project_headers:
                    current_section = "projects_highlights"
                else:
                    current_section = header.title()
                header_found = True
                break

        # If not a header and within a section, add the line to that section.
        if not header_found and current_section and clean_line:
            sections[current_section].append(line.rstrip())  # Preserve original formatting.
    return dict(sections)


# ===================== EDUCATION MATCHING IMPROVEMENTS =====================
def normalize_degree(degree: str) -> str:
    """
    Map degree variations to standard names.

    :param degree: Degree string to normalize.
    :return: Normalized degree string.
    """
    return DEGREE_MAPPING.get(degree.lower(), degree.lower())


def parse_education(education_lines: List[str]) -> Dict[str, Any]:
    """
    Extracts and normalizes the highest degree from education lines.

    :param education_lines: Lines from the education section.
    :return: Dictionary with normalized degree.
    """
    education = {'degree': None}
    if not education_lines:
        return education

    degrees_found: Set[str] = set()
    for line in education_lines:
        for word in line.split():
            normalized = DEGREE_MAPPING.get(word.lower(), word.lower())
            # Check if the normalized degree (in title case) is in the defined hierarchy.
            if normalized.title() in DEGREE_HIERARCHY:
                degrees_found.add(normalized.title())

    if degrees_found:
        # Choose the highest degree based on the hierarchy order.
        education['degree'] = min(degrees_found, key=lambda x: DEGREE_HIERARCHY.index(x))

    return education


def parse_experience(experience_lines: List[str]) -> List[str]:
    """
    Extract experience entries exactly as formatted in the resume.

    :param experience_lines: Lines from the experience section.
    :return: List of experience entries.
    """
    experiences = []
    current_entry = []

    # Compile regex patterns outside the loop for slight efficiency gain.
    pattern1 = re.compile(r'^[A-Z]{3,} \d{4}.*$')
    pattern2 = re.compile(r'^\d{4}')

    for line in experience_lines:
        if pattern1.match(line) or pattern2.match(line):  # Detect job start periods
            if current_entry:
                experiences.append("\n".join(current_entry).strip())  # Store previous entry
            current_entry = [line]  # Start new job entry
        else:
            current_entry.append(line)  # Append continuation lines

    if current_entry:
        experiences.append("\n".join(current_entry).strip())

    return experiences


# ===================== SKILL EXTRACTION FROM RESUME =====================
def extract_skills(text: str) -> List[str]:
    """
    Extract skills from the resume using a single PhraseMatcher.

    :param text: Resume text.
    :return: Sorted list of detected skills.
    """
    doc = nlp(text.lower())
    skills: Set[str] = set()

    # Use the prebuilt global SKILL_MATCHER.
    matches = SKILL_MATCHER(doc)
    for _, start, end in matches:
        skill_text = doc[start:end].text.lower()
        # Look up the canonical skill or fallback to title-cased text.
        skills.add(SKILL_MAPPING.get(skill_text, skill_text.title()))
    return sorted(skills, key=lambda x: x.lower())


def extract_skill_section(text: str) -> List[str]:
    """
    Extract text from sections that likely list skills.

    :param text: Resume text.
    :return: List of skill lines.
    """
    patterns = [
        r'(?i)(?:technical|key|core)\s*skills:?\s*\n(.*?)(?=\n\s*\n|$)',
        r'(?i)competencies:?\s*\n(.*?)(?=\n\s*\n|$)',
        r'(?i)expertise:?\s*\n(.*?)(?=\n\s*\n|$)'
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return [line.strip() for line in match.group(1).split('\n') if line.strip()]
    return []


# ===================== PROJECTS EXTRACTION =====================
def parse_projects_highlights(project_lines: List[str]) -> List[str]:
    """
    Parse the projects/highlights section using multiple detection strategies.

    :param project_lines: Lines from the projects/highlights section.
    :return: List of formatted project entries.
    """
    projects = []
    current_project = []
    in_project = False

    for line in project_lines:
        # Detect project starters based on dates, bullet points, or key phrases.
        if (re.match(r'^(.*\d{4}.*?[-–].*|•|\u2022)', line) or
                'project' in line.lower() or
                re.search(r'\b(developed|created|built)\b', line.lower())):
            if current_project:
                projects.append("\n".join(current_project).strip())
            current_project = [line]
            in_project = True
        elif in_project:
            # Handle continuation lines that are bullet points or further description.
            if re.match(r'^\s*[-•*]', line):
                current_project.append(line.strip())
            else:
                current_project[-1] += " " + line.strip()

    if current_project:
        projects.append("\n".join(current_project).strip())

    # Fallback: If no projects detected, split by bullet points.
    if not projects:
        bullet_points = re.split(r'\n\s*[\u2022•*-]\s*', '\n'.join(project_lines))
        projects = [bp.strip() for bp in bullet_points if bp.strip()]

    return projects


# ===================== MAIN ANALYSIS FUNCTION =====================
def analyze_resume(text: str) -> Dict[str, Any]:
    """
    Analyze the resume text and extract structured information.

    :param text: The complete resume text.
    :return: Dictionary containing education, experience, skills, and projects/highlights.
    """
    sections = extract_sections(text)

    # Extract skills both from a dedicated 'Skills' section (if exists) and the full text.
    section_skills = extract_skills(' '.join(sections.get('Skills', [])))
    full_text_skills = extract_skills(text)

    experience_section = sections.get('Experience', [])
    experience_data = parse_experience(experience_section) if experience_section else []

    return {
        'education': parse_education(sections.get('Education', [])),
        'experience': experience_data,
        'skills': list(set(section_skills + full_text_skills)),
        'projects_highlights': parse_projects_highlights(sections.get('projects_highlights', []))
    }


# ===================== MATCHING FUNCTION =====================
def analyze_match(resume_data: Dict[str, Any], job_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare resume data with job data using skill matching and education level.

    :param resume_data: Structured resume data (from analyze_resume).
    :param job_data: Job data including required_skills and education requirements.
    :return: Dictionary with matching scores and details.
    """
    # Skill matching: use lowercase sets for consistency.
    resume_skills = {s.lower() for s in resume_data.get("skills", [])}
    job_skills = {s.lower() for s in job_data.get("required_skills", [])}
    skill_match = (len(resume_skills & job_skills) / len(job_skills) * 100) if job_skills else 100
    boosted_skill = min(skill_match * SKILL_BOOST, 100)

    # Education matching: if no requirement, consider it met.
    resume_degree = resume_data.get("education", {}).get("degree", "")
    job_degree = job_data.get("education", "")

    if not job_degree:
        edu_score = 100
        education_match = "Met (No requirement)"
    else:
        try:
            job_level = DEGREE_HIERARCHY.index(job_degree)
            resume_level = DEGREE_HIERARCHY.index(resume_degree)
            edu_score = 100 if resume_level <= job_level else 0
        except ValueError:
            edu_score = 0  # Unknown degree found
        education_match = "Met" if edu_score == 100 else "Not met"

    # Composite score combining skills and education.
    composite = (0.8 * boosted_skill) + (0.2 * edu_score)
    final_match = 100 if composite >= COMPOSITE_THRESHOLD else (composite / COMPOSITE_THRESHOLD) * 100

    return {
        "skill_match": f"{boosted_skill:.1f}%",
        "education_match": education_match,
        "composite_score": f"{composite:.1f}%",
        "final_match": f"{final_match:.1f}%",
        "missing_skills": sorted(job_skills - resume_skills),
        "resume_summary": {"total_skills": len(resume_skills)}
    }


# ===================== EXAMPLE USAGE =====================
if __name__ == "__main__":
    sample_resume = """
    John Doe

    EDUCATION
    Bachelor of Science in Computer Science
    University of Toronto 2018-2022

    TECHNICAL SKILLS
    Python, Java, SQL, React, AWS, Machine Learning, English

    WORK EXPERIENCE
    Google – Mountain View, CA | Software Engineer | Jan 2022-Present
    Developed machine learning models using TensorFlow and Python.
    """
    result = analyze_resume(sample_resume)
    print("Education:", result['education'])
    print("Skills:", result['skills'])
    print("Experience:", result['experience'])
