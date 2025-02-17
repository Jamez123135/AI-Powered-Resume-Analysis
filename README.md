# CareerConnect - AI-Powered Resume Analysis

🚀 **CareerConnect** is an **AI-powered resume analysis platform** that helps job seekers optimize their resumes by comparing them with job descriptions. Recruiters can also upload multiple resumes to rank candidates based on skill compatibility.

---

## 🔍 Features

✅ **Resume Parsing & Skill Extraction** – Uses **SpaCy NLP** to extract key skills from uploaded PDFs.  
✅ **Job Description Matching** – Compares resume skills with job descriptions using **PhraseMatcher & NER**.  
✅ **Compatibility Scoring** – Calculates a match percentage and provides feedback.  
✅ **Recruiter Dashboard** – Upload multiple resumes and rank candidates by job fit.  
✅ **Modern UI** – Built with **Bootstrap** for a clean, responsive user interface.  

---

## 🛠️ Tech Stack

| Category         | Technologies Used  |
|----------------|-------------------|
| **Frontend** | HTML, CSS, Bootstrap |
| **Backend** | Flask (Python), Jinja2 |
| **NLP & AI** | SpaCy, PhraseMatcher, Named Entity Recognition (NER) |
| **Database** | SQLite / PostgreSQL |
| **File Handling** | PyPDF2 |
| **Dev Tools** | Git, GitHub, PyCharm |

---

## 🚀 Getting Started

### 1️⃣ Clone the Repository
```sh
git clone https://github.com/jamez123135/careerconnect.git
cd careerconnect
```

### 2️⃣ Install Dependencies
Make sure you have Python installed, then run:
```sh
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 3️⃣ Run the Application
```sh
flask run
```
Then, open **http://127.0.0.1:5000/** in your browser.

---

## 📂 Project Structure
```
careerconnect/
│── static/                 # CSS & JS files  
│── templates/              # HTML templates (Job Seekers, Recruiters)  
│── app.py                  # Main Flask app  
│── data_base.py            # Skills database & matching logic  
│── requirements.txt        # Dependencies  
│── README.md               # Project documentation  
```

---

## 📝 Usage

1️⃣ **Job Seekers:** Upload your resume and a job description to get a **match percentage** and **missing skills**.  
2️⃣ **Recruiters:** Upload multiple resumes and rank candidates by **job fit**.  
3️⃣ **Skill Analysis:** Extracts key **technical & soft skills** from resumes using **AI/NLP**.  

---

## Contributors

1️⃣ ***James Akhator*** (Lead Developer).  
2️⃣ ***Johnpaul Akhator***    

---

## 🎯 Future Enhancements

🔹 **Machine Learning Model** – Improve skill matching accuracy using ML techniques.  
🔹 **Resume Recommendations** – Provide tailored resume improvement suggestions.  
🔹 **API Integration** – Allow third-party ATS systems to integrate with CareerConnect.  

---

## 📬 Contact & Contributions
💡 Want to contribute? Feel free to submit a **pull request**!  
📩 For inquiries, contact **joakhator@upei.ca**  
