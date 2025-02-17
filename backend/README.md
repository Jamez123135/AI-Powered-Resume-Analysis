AI-Powered Resume Analysis Platform
Project Overview
This AI-powered web application analyzes resumes against job descriptions to provide a compatibility score. It serves both job seekers and recruiters by extracting relevant skills, experiences, and education details. Recruiters can upload multiple resumes and rank them based on job fit.
Features
Resume Parsing: Extracts skills, experience, and education details.
Job Description Matching: Compares extracted resume data with job descriptions to calculate a match percentage.
Recruiter Dashboard: Allows recruiters to upload multiple resumes and rank candidates based on compatibility.
Job Seeker Dashboard: Enables job seekers to analyze their resume against a specific job posting.
Modern UI: A clean and responsive user interface built with Bootstrap and JavaScript.
Tech Stack
Backend: Python (Flask)
Frontend: HTML, CSS, JavaScript, Bootstrap
Parsing & Analysis: Natural Language Processing (NLP) techniques
Storage: File uploads handled with Flask
Setup Instructions
1. Clone the Repository
git clone https://github.com/jamez123135/resume-analysis.git
cd resume-analysis

2. Create a Virtual Environment & Install Dependencies
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt

3. Run the Flask App
python app.py

4. Access the Web App
Open http://127.0.0.1:5000/ in your browser.
Project Structure
resume-analysis/
│── app.py                 # Main Flask application
│── requirements.txt       # Python dependencies
│── static/                # CSS, JavaScript, images
│── templates/             # HTML templates
│── uploads/               # Directory for uploaded resumes
└── README.md              # Project documentation

Future Enhancements
Implement AI-powered recommendations for skill improvement
Improve resume parsing accuracy with ML models
Support additional file formats (e.g., DOCX)
Contributors
James Akhator (Lead Developer)
John-Paul Akhator 
Open for contributions! Fork the repo and submit a pull request.
License
This project is open-source under the MIT License.
