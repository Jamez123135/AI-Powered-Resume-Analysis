from flask import Flask, request, jsonify
import spacy
import re
from collections import defaultdict
from spacy.matcher import PhraseMatcher
from data_base import SKILLS_DB
app = Flask(__name__)

# Load NLP model
nlp = spacy.load("en_core_web_sm")
from resume_analysis import SKILL_MAPPING  # Import shared skills DB
SKILL_MAPPING = defaultdict(list)
for skill, aliases in SKILLS_DB.items():
    for alias in aliases:
        SKILL_MAPPING[alias].append(skill)
    SKILL_MAPPING[skill.lower()].append(skill)
matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
patterns = [nlp.make_doc(alias) for aliases in SKILLS_DB.values() for alias in aliases]
matcher.add("SKILLS", None, *patterns)
# ===================== JOB DESCRIPTION PARSER =====================
def parse_job_description(job_text):
    """Optimized job parser with phrase matching and lemmatization"""
    parsed_job = {
        "required_skills": [],
        "years_experience": None,
        "education": None,
        "skills_match_percentage": 0
    }

    doc = nlp(job_text.lower())
    skills_found = set()

    # 1. Phrase-based matching
    matches = matcher(doc)
    for match_id, start, end in matches:
        span = doc[start:end]
        if span.text in SKILL_MAPPING:
            skills_found.update(SKILL_MAPPING[span.text])

    # 2. Lemmatization-based matching
    for token in doc:
        lemma = token.lemma_.lower()
        if lemma in SKILL_MAPPING:
            skills_found.update(SKILL_MAPPING[lemma])

    # 3. Handle compound nouns (e.g., "machine learning")
    for chunk in doc.noun_chunks:
        chunk_text = chunk.text.lower()
        if chunk_text in SKILL_MAPPING:
            skills_found.update(SKILL_MAPPING[chunk_text])

    # Calculate match percentage (improved logic)
    total_mentions = len([token for token in doc if token.text in SKILL_MAPPING])
    matched_skills = len(skills_found)

    if total_mentions > 0:
        parsed_job["skills_match_percentage"] = min((matched_skills / total_mentions) * 100, 100)

    parsed_job["required_skills"] = sorted(skills_found)

    # Improved experience extraction
    experience_pattern = r'(\d+[\+\.]?\d*)\s+(years?|yrs?)(?:\s+of)?\s+(experience|exp|industry)'
    experience_match = re.search(experience_pattern, job_text, re.IGNORECASE)
    if experience_match:
        years = experience_match.group(1)
        parsed_job["years_experience"] = f"{years} years"

    # Enhanced education pattern
    education_pattern = r'\b(PhD|Doctorate|M\.?S\.?|M\.?Eng|M\.?A\.?|Master|B\.?S\.?|B\.?A\.?|B\.?Eng|Bachelor)\b'
    education_match = re.search(education_pattern, job_text, re.IGNORECASE)
    if education_match:
        degree = education_match.group(1).title()
        # Normalize degree names
        degree = re.sub(r'^M\.?S\.?$', 'Master', degree)
        degree = re.sub(r'^B\.?S\.?$', 'Bachelor', degree)
        parsed_job["education"] = degree

    return parsed_job
# ===================== FLASK ROUTE FOR JOB DESCRIPTION =====================
@app.route('/upload_job_description', methods=['POST'])
def upload_job_description():
    try:
        # Handle both form-data and JSON
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
        return jsonify({
            "error": f"Invalid request format: {str(e)}"
        }), 400
# Run Flask app
if __name__ == "__main__":
    app.run(debug=True)



"import spacy
import re
from collections import defaultdict
from spacy.matcher import PhraseMatcher

# Load the spaCy model once.
nlp = spacy.load("en_core_web_sm")
from data_base import SKILLS_DB

# ===================== NORMALIZE SKILL KEYS =====================
# Force keys to lower-case for case-insensitive matching.
SKILL_MAPPING = {
    variation.lower(): canonical
    for canonical, variations in SKILLS_DB.items()
    for variation in variations
}
SKILL_PATTERNS = [nlp.make_doc(variation) for variants in SKILLS_DB.values() for variation in variants]
SKILL_MATCHER = PhraseMatcher(nlp.vocab, attr="LOWER")
SKILL_MATCHER.add("SKILL", SKILL_PATTERNS)

# ===================== OTHER PATTERNS & CONSTANTS =====================
DEGREE_PATTERNS = re.compile(
    r"\b(B\.?S\.?|B\.?A\.?|M\.?S\.?|M\.?A\.?|Ph\.?D\.?|Bachelor|Master|"
    r"B\.?Eng|M\.?Eng|B\.?Tech|M\.?Tech|B\.?Sc|M\.?Sc)\b",
    re.IGNORECASE
)

UNIVERSITY_NAMES = {
    'university', 'college', 'institute', 'school',
    'mit', 'stanford', 'harvard', 'upei', 'toronto', 'waterloo'
}


# ===================== JOB SKILLS EXTRACTION =====================
def extract_job_skills(job_text):
    """Extract skills from a job description using SKILLS_DB."""
    job_skills = set()
    doc = nlp(job_text.lower())

    # Match skills token-by-token
    for token in doc:
        if token.text in SKILL_MAPPING:
            job_skills.add(SKILL_MAPPING[token.text])

    # Also check for multi-word skills (e.g., "machine learning")
    for skill, variations in SKILLS_DB.items():
        for variation in variations:
            if variation in job_text.lower():
                job_skills.add(skill)

    # --- AUTOMATIC ENGLISH REQUIREMENT ---
    if "english" in job_text.lower():
        job_skills.add("English")

    return list(job_skills)


# ===================== SKILL COMPARISON =====================
def compare_skills(resume_skills, job_skills):
    """Compare resume skills with job skills."""
    resume_skills = set(skill.lower() for skill in resume_skills)
    job_skills = set(skill.lower() for skill in job_skills)
    match_percentage = (len(resume_skills & job_skills) / len(job_skills)) * 100 if job_skills else 0
    return {
        "match_percentage": f"{match_percentage:.1f}%",
        "matched_skills": sorted(resume_skills & job_skills),
        "missing_skills": sorted(job_skills - resume_skills)
    }


# ===================== SECTION EXTRACTION =====================
# ===================== SECTION EXTRACTION =====================
def extract_sections(text):
    """
    Extract sections from resume text based on common headers.
    All headers indicating experience are mapped to the key "Experience".
    """
    # Define headers that indicate the experience section.
    experience_headers = [
        'experience', 'work experience', 'employment', 'professional experience',
        'career', 'work history', 'professional background'
    ]
    # Other section headers.
    other_headers = [
        'education', 'skills', 'projects', 'summary', 'academic', 'roles',
        'technical expertise', 'core competencies'
    ]
    project_headers = [
        'projects', 'personal projects', 'extracurricular',
        'highlights', 'notable work', 'achievements',
        'projects_highlights'
    ]
    all_headers = experience_headers + project_headers + other_headers

    sections = defaultdict(list)
    current_section = None

    for line in text.split('\n'):
        clean_line = line.strip()
        lower_line = clean_line.lower()
        header_found = False
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
        if not header_found and current_section and clean_line:
            sections[current_section].append(line.rstrip())  # Preserve the original formatting.
    return sections


SKILL_BOOST = 1.1  # 30% boost
COMPOSITE_THRESHOLD = 80.0
DEGREE_HIERARCHY = [
    "PhD", "Doctorate", "MD", "JD", "Master", "MBA", "MSc", "MA",
    "BSc", "BA", "BEng", "Bachelor", "Associate", "Diploma", "Certificate"
]
DEGREE_PATTERNS = re.compile(r'(?i)\b(?:' + '|'.join(DEGREE_HIERARCHY) + r')\b')


# ===================== EDUCATION MATCHING IMPROVEMENTS =====================
def normalize_degree(degree):
    """Map degree variations to standard names"""
    return DEGREE_MAPPING.get(degree.lower(), degree.lower())


DEGREE_MAPPING = {
    'bs': 'Bachelor', 'bsc': 'Bachelor', 'b.a.': 'Bachelor', 'ba': 'Bachelor',
    'ms': 'Master', 'msc': 'Master', 'm.a.': 'Master', 'ma': 'Master',
    'phd': 'PhD', 'doctorate': 'PhD', 'beng': 'Bachelor', 'meng': 'Master'
}


def parse_education(education_lines):
    """Extracts and normalizes the highest degree"""
    education = {'degree': None}
    if not education_lines:
        return education

    degrees_found = set()
    for line in education_lines:
        for word in line.split():
            normalized = DEGREE_MAPPING.get(word.lower(), word.lower())
            if normalized.title() in DEGREE_HIERARCHY:
                degrees_found.add(normalized.title())

    if degrees_found:
        # Get highest degree using hierarchy order
        education['degree'] = min(
            degrees_found,
            key=lambda x: DEGREE_HIERARCHY.index(x)
        )

    return education


def parse_experience(experience_lines):
    """
    Extract experience section exactly as formatted in the resume.
    """
    experiences = []
    current_entry = []

    for line in experience_lines:
        if re.match(r'^[A-Z]{3,} \d{4}.*$', line) or re.match(r'^\d{4}', line):  # Detecting job start periods
            if current_entry:
                experiences.append("\n".join(current_entry).strip())  # Store previous entry
            current_entry = [line]  # Start new job entry
        else:
            current_entry.append(line)  # Append description lines

    if current_entry:
        experiences.append("\n".join(current_entry).strip())  # Add last entry

    return experiences


# ===================== SKILL EXTRACTION FROM RESUME =====================
# Rebuild SKILL_MAPPING for case-insensitive matching.
SKILL_MAPPING = {variant: skill for skill, variants in SKILLS_DB.items() for variant in variants}


def extract_skills(text):
    """Improved skill extraction using single matcher"""
    doc = nlp(text.lower())
    skills = set()

    # Use global SKILL_MATCHER instead of creating new one
    matches = SKILL_MATCHER(doc)
    for _, start, end in matches:
        skill_text = doc[start:end].text.lower()
        skills.add(SKILL_MAPPING.get(skill_text, skill_text.title()))

    # Rest of your existing regex-based extraction logic...
    return sorted(skills, key=lambda x: x.lower())


def extract_skill_section(text):
    """Extract text from sections that likely list skills."""
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
def parse_projects_highlights(project_lines):
    """
    Improved project parsing with multiple detection strategies
    """
    projects = []
    current_project = []
    in_project = False

    project_start_pattern = re.compile(
        r'^(.*?)\s*'  # Project name
        r'(\(.*?\)|\[.*?\]|\d{4}-\d{4}|-\s*present)?\s*'  # Optional date/context
        r'[:•\-]?\s*$',
        re.IGNORECASE
    )

    for line in project_lines:
        # Detect project starters: dates, bullets, or key phrases
        if (re.match(r'^(.*\d{4}.*?[-–].*|•|\u2022)', line) or
                'project' in line.lower() or
                re.search(r'\b(developed|created|built)\b', line.lower())):

            if current_project:
                projects.append("\n".join(current_project).strip())
            current_project = [line]
            in_project = True
        elif in_project:
            # Handle continuation lines
            if re.match(r'^\s*[-•*]', line):
                current_project.append(line.strip())
            else:
                current_project[-1] += " " + line.strip()

    if current_project:
        projects.append("\n".join(current_project).strip())

    # Fallback: Split by bullet points if no projects detected
    if not projects:
        bullet_points = re.split(r'\n\s*[\u2022•*-]\s*', '\n'.join(project_lines))
        projects = [bp.strip() for bp in bullet_points if bp.strip()]

    return projects


# ===================== MAIN ANALYSIS FUNCTION =====================
def analyze_resume(text):
    sections = extract_sections(text)
    print("=" * 40)
    print("Detected Sections:", sections.keys())
    if 'projects_highlights' in sections:
        print("Raw Project Lines:", sections['projects_highlights'])
    section_skills = extract_skills(' '.join(sections.get('Skills', [])))
    full_text_skills = extract_skills(text)
    experience_data = []
    experience_section = sections.get('Experience', [])
    if experience_section:
        experience_data = parse_experience(experience_section)
    return {
        'education': parse_education(sections.get('Education', [])),
        'experience': experience_data,
        'skills': list(set(section_skills + full_text_skills)),
        'projects_highlights': parse_projects_highlights(sections.get('projects_highlights', []))
    }


# ===================== MATCHING FUNCTION WITH EDUCATION & 80% THRESHOLD =====================
def analyze_match(resume_data, job_data):
    """Improved matching logic with hierarchy-based education check"""
    # Skill matching (keep your existing logic)
    resume_skills = set(s.lower() for s in resume_data.get("skills", []))
    job_skills = set(s.lower() for s in job_data.get("required_skills", []))
    skill_match = (len(resume_skills & job_skills) / len(job_skills) * 100) if job_skills else 100
    boosted_skill = min(skill_match * SKILL_BOOST, 100)

    # Enhanced education matching
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
            edu_score = 0  # Handle unknown degrees

        education_match = "Met" if edu_score == 100 else "Not met"

    # Composite calculation (keep your existing logic)
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
"


def parse_education(education_lines):
    """Extract education details from the education section."""
    education = {'degree': None, 'university': None, 'dates': None}
    if not education_lines:
        return education
    edu_text = ' '.join(education_lines)
    degree_match = DEGREE_PATTERNS.search(edu_text)
    if degree_match:
        education['degree'] = degree_match.group(0).strip()
    doc = nlp(edu_text)
    for ent in doc.ents:
        if ent.label_ == 'ORG' and any(word in ent.text.lower() for word in UNIVERSITY_NAMES):
            education['university'] = ent.text
            break
    date_pattern = r'(\d{4}[-–](?:Present|\d{4})|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}\b)'
    dates = re.findall(date_pattern, edu_text, re.IGNORECASE)
    if dates:
        education['dates'] = dates[0]
    return education




from flask import Flask, request, jsonify
import spacy
import re
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Job Seeker Analysis</title>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <h1>Job Seeker Resume Analysis</h1>

    <form id="jobseeker-form" enctype="multipart/form-data">
        <label for="resume">Upload Resume (PDF):</label>
        <input type="file" id="resume" name="resume" accept=".pdf" required><br><br>

        <label for="job-description">Paste Job Description:</label>
        <textarea id="job-description" name="job_description" rows="5" required></textarea><br><br>

        <button type="submit">Analyze Resume</button>
    </form>

    <h2>Results</h2>
    <div id="results"></div>


</body>
</html>


app = Flask(__name__)
# ===================== SKILLS DATABASE =====================
SKILLS_DB = {
    # ========== TECHNICAL SKILLS ==========
    'Python': ['python', 'py', 'python3', 'cpython', 'ironpython'],
    'Java': ['java', 'j2ee', 'javase', 'java ee', 'spring framework'],
    'JavaScript': ['javascript', 'js', 'es6', 'ecmascript', 'typescript', 'ts'],
    'C++': ['c++', 'cpp', 'c plus plus', 'stl'],
    'C#': ['c#', 'csharp', 'dotnet', '.net'],
    'SQL': ['sql', 't-sql', 'pl/sql', 'sqlite', 'transact-sql'],
    'R': ['r', 'rlang', 'rstudio'],
    'Swift': ['swift', 'swiftui'],
    'Kotlin': ['kotlin', 'kt'],
    'Go': ['go', 'golang'],

    # Web Development
    'HTML': ['html', 'html5'],
    'CSS': ['css', 'css3', 'sass', 'scss', 'less'],
    'React': ['react', 'react.js', 'reactjs', 'next.js'],
    'Angular': ['angular', 'angularjs'],
    'Vue.js': ['vue', 'vue.js', 'vuejs'],
    'Node.js': ['node', 'node.js', 'express.js'],
    'Django': ['django', 'djangorest'],
    'Flask': ['flask'],
    'Spring Boot': ['spring', 'springboot'],

    # Mobile Development
    'Android': ['android', 'android sdk'],
    'iOS': ['ios', 'swiftui', 'cocoa touch'],
    'React Native': ['react native', 'rn'],
    'Flutter': ['flutter', 'dart'],

    # Cloud & DevOps
    'AWS': ['aws', 'amazon web services', 'ec2', 's3', 'lambda'],
    'Azure': ['azure', 'microsoft azure'],
    'GCP': ['gcp', 'google cloud'],
    'Docker': ['docker', 'containerization'],
    'Kubernetes': ['kubernetes', 'k8s'],
    'Terraform': ['terraform', 'iac'],
    'Ansible': ['ansible'],
    'Jenkins': ['jenkins', 'ci/cd'],

    # Databases
    'MySQL': ['mysql', 'mariadb'],
    'PostgreSQL': ['postgres', 'postgresql', 'postgres db'],
    'MongoDB': ['mongodb', 'mongo'],
    'Oracle': ['oracle db', 'oracle database'],
    'Redis': ['redis'],
    'Cassandra': ['cassandra', 'apache cassandra'],

    # Data Science
    'Machine Learning': ['ml', 'machine learning', 'deep learning'],
    'TensorFlow': ['tensorflow', 'tf'],
    'PyTorch': ['pytorch'],
    'Pandas': ['pandas'],
    'NumPy': ['numpy'],
    'Tableau': ['tableau'],
    'Power BI': ['powerbi', 'power bi'],

    # Networking & Security
    'Cybersecurity': ['cybersecurity', 'infosec'],
    'Ethical Hacking': ['pentesting', 'penetration testing'],
    'Cisco': ['ccna', 'ccnp', 'cisco ios'],
    'Firewall': ['firewalls', 'iptables'],
    'VPN': ['vpn', 'openvpn'],

    # ========== SOFT SKILLS ==========
    'Communication': ['verbal communication', 'written communication', 'presentation skills'],
    'Leadership': ['team leadership', 'people management', 'mentoring'],
    'Problem Solving': ['troubleshooting', 'critical thinking', 'root cause analysis'],
    'Teamwork': ['collaboration', 'cross-functional teams', 'team player'],
    'Time Management': ['deadline-oriented', 'prioritization', 'multitasking'],
    'Creativity': ['innovation', 'design thinking', 'ideation'],

    # ========== TOOLS & PLATFORMS ==========
    'Microsoft Office': ['excel', 'word', 'powerpoint', 'outlook', 'ms office'],
    'Google Workspace': ['google docs', 'google sheets', 'g suite'],

    'Adobe Creative Suite': ['photoshop', 'illustrator', 'indesign', 'xd'],
    'Figma': ['figma'],
    'Sketch': ['sketch'],

    'Jira': ['jira', 'atlassian'],
    'Trello': ['trello'],
    'Asana': ['asana'],

    'Salesforce': ['salesforce', 'sfdc'],
    'HubSpot': ['hubspot'],

    'Git': ['git', 'github', 'gitlab', 'bitbucket'],

    # ========== METHODOLOGIES ==========
    'Agile': ['scrum', 'sprint planning', 'agile methodology'],
    'Waterfall': ['waterfall methodology'],
    'Six Sigma': ['lean six sigma', 'dmaic', 'belts'],
    'ITIL': ['itil', 'it infrastructure library'],
    'DevOps': ['devsecops', 'gitops'],

    # ========== BUSINESS & MANAGEMENT ==========
    'Project Management': ['project planning', 'stakeholder management', 'pmbok'],
    'Digital Marketing': ['seo', 'sem', 'ppc', 'social media marketing'],
    'Sales': ['business development', 'account management', 'salesforce'],
    'Financial Analysis': ['financial modeling', 'valuation', 'fp&a'],
    'Supply Chain': ['logistics', 'inventory management', 'procurement'],

    # ========== CREATIVE SKILLS ==========
    'Graphic Design': ['visual design', 'layout design', 'branding'],
    'Video Editing': ['premiere pro', 'final cut pro', 'video production'],
    'Copywriting': ['content writing', 'technical writing', 'blogging'],

    # ========== CERTIFICATIONS ==========
    'PMP': ['project management professional'],
    'AWS Certified': ['aws solutions architect', 'aws developer'],
    'CISSP': ['certified information systems security professional'],
    'CompTIA': ['comptia a+', 'security+', 'network+'],
    'Google Analytics': ['ga', 'google analytics certified'],

    # ========== LANGUAGES ==========
    'English': ['english', 'fluent english'],
    'Spanish': ['spanish', 'español'],
    'French': ['french', 'français'],
    'Mandarin': ['mandarin', 'chinese'],

    # ========== INDUSTRY-SPECIFIC ==========
    'EMR': ['electronic medical records', 'epic', 'cerner'],
    'HIPAA': ['hipaa compliance'],
    'Patient Care': ['patient advocacy', 'clinical skills'],

    'Curriculum Development': ['lesson planning', 'instructional design'],
    'Classroom Management': ['student engagement', 'behavior management'],

    'Lean Manufacturing': ['5s', 'kaizen', 'continuous improvement'],
    'CAD': ['autocad', 'solidworks', 'fusion 360'],

    'Legal Research': ['westlaw', 'lexisnexis'],
    'Contract Law': ['contract drafting', 'clm'],

    'Blockchain': ['smart contracts', 'solidity', 'web3'],
    'IoT': ['internet of things', 'arduino', 'raspberry pi'],
    'AI': ['artificial intelligence', 'generative ai', 'llms'],

    'Public Speaking': ['keynote speaking', 'presentation skills'],
    'Event Planning': ['event coordination', 'venue management'],
    'Teaching': ['tutoring', 'workshop facilitation']
}

# Load NLP model
nlp = spacy.load("en_core_web_sm")
from resume_analysis import SKILL_MAPPING  # Import shared skills DB


def parse_job_description(job_text):
    """Enhanced job parser using resume skills DB"""
    parsed_job = {
        "required_skills": [],
        "years_experience": None,
        "education": None
    }

    # Skill extraction using shared DB
    doc = nlp(job_text.lower())
    for token in doc:
        if token.text in SKILL_MAPPING:
            parsed_job["required_skills"].append(SKILL_MAPPING[token.text])

    # Remove duplicates
    parsed_job["required_skills"] = list(set(parsed_job["required_skills"]))

    # Rest of your existing parsing logic...
    return parsed_job

# ===================== JOB DESCRIPTION PARSER =====================
def parse_job_description(job_text):
    """Enhanced job parser with scaled skills match percentage directly in the main function."""
    parsed_job = {
        "required_skills": [],
        "years_experience": None,
        "education": None,
        "skills_match_percentage": 0  # Added for scaled skills match percentage
    }

    # Normalize job text
    doc = nlp(job_text.lower())
    skills_found = set()
    total_skills_in_description = 0  # To count skills in the description

    # Check each word/phrase in the job description
    for token in doc:
        for skill, keywords in SKILLS_DB.items():
            if token.text in keywords or token.text == skill.lower():
                skills_found.add(skill)  # Add recognized skills
                total_skills_in_description += 1


    # Calculate the match percentage (based on total skills matched vs total in description)
    if total_skills_in_description > 0:
        match_percentage = (len(skills_found) / total_skills_in_description) * 100
    else:
        match_percentage = 0


    # Scale the match percentage directly in the function
    if match_percentage >= 70:
        scaled_percentage = (match_percentage - 70) / 30 * 100 + 70
    elif match_percentage >= 60:
        scaled_percentage = (match_percentage - 60) / 10 * 15 + 70
    elif match_percentage >= 50:
        scaled_percentage = (match_percentage - 50) / 10 * 21 + 50
    elif match_percentage >= 40:
        scaled_percentage = (match_percentage - 40) / 10 * 17 + 29
    elif match_percentage >= 30:
        scaled_percentage = (match_percentage - 30) / 10 * 14 + 15
    elif match_percentage >= 20:
        scaled_percentage = (match_percentage - 20) / 10 * 7 + 0
    else:
        scaled_percentage = 20  # Below 20% returns 0

    parsed_job["skills_match_percentage"] = scaled_percentage

    parsed_job["required_skills"] = sorted(skills_found)  # Sort for consistency

    # Extract years of experience
    experience_pattern = r"(\d+)\+?\s+(years?|yrs?)\s+of\s+(experience|exp)"
    experience_match = re.search(experience_pattern, job_text, re.IGNORECASE)
    if experience_match:
        parsed_job["years_experience"] = experience_match.group(1) + " years"

    # Extract education requirements
    education_pattern = r"(Bachelor's|Master's|Ph\.D)\s+degree\s+in\s+([\w\s]+)"
    education_match = re.search(education_pattern, job_text, re.IGNORECASE)
    if education_match:
        parsed_job["education"] = f"{education_match.group(1)} in {education_match.group(2)}"

    return parsed_job


# ===================== FLASK ROUTE FOR JOB DESCRIPTION =====================
@app.route('/upload_job_description', methods=['POST'])
def upload_job_description():
    try:
        # Handle both form-data and JSON
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
        return jsonify({
            "error": f"Invalid request format: {str(e)}"
        }), 400
# Run Flask app
if __name__ == "__main__":
    app.run(debug=True)
