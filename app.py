import streamlit as st
import os
from pypdf import PdfReader
import docx
import nltk
import re

# ---------------- Ensure 'punkt' tokenizer is available ----------------
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt")

# ---------------- Setup ----------------
UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.mkdir(UPLOAD_FOLDER)

# ---------------- Create default skills.txt if missing ----------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILLS_FILE = os.path.join(SCRIPT_DIR, "skills.txt")

DEFAULT_SKILLS = [
    "Python", "Java", "C++", "SQL", "HTML", "CSS", "JavaScript",
    "React", "Django", "Machine Learning", "Data Analysis", "AWS",
    "Git", "TensorFlow", "PyTorch"
]

if not os.path.exists(SKILLS_FILE):
    with open(SKILLS_FILE, "w") as f:
        f.write("\n".join(DEFAULT_SKILLS))

# ---------------- Extract Resume Text ----------------
def extract_text(file):
    if file.name.endswith(".pdf"):
        text = ""
reader = PdfReader(file)
for page in reader.pages:
    page_text = page.extract_text()

            if page_text:
                text += page_text
        return text.lower()
    elif file.name.endswith(".docx"):
        doc = docx.Document(file)
        return " ".join([p.text for p in doc.paragraphs]).lower()
    else:
        st.error("Only PDF and DOCX supported!")
        return ""

# ---------------- Skill Matching ----------------
def load_skills():
    with open(SKILLS_FILE, "r") as f:
        return [s.strip() for s in f.readlines()]

def find_skills(resume_text):
    skills = load_skills()
    matched = [s for s in skills if s.lower() in resume_text]
    missing = [s for s in skills if s.lower() not in resume_text]
    return matched, missing

# ---------------- Resume Section Feedback ----------------
def structure_feedback(resume_text):
    sections = ['experience', 'education', 'projects', 'skills', 'summary', 'objective', 'certifications']
    present = [sec for sec in sections if sec in resume_text]
    missing = [sec for sec in sections if sec not in resume_text]
    return present, missing

# ---------------- Sentence Improvement ----------------
ACTION_VERBS = ["led","implemented","optimized","developed","designed","managed","automated","created","built"]

def suggest_sentences(resume_text):
    sentences = nltk.tokenize.sent_tokenize(resume_text)
    suggestions = []
    for sent in sentences:
        sent_clean = sent.strip()
        if len(sent_clean.split()) < 5 or any(v in sent_clean for v in ACTION_VERBS):
            continue
        suggestions.append(f"Rewrite using action verbs + impact: '{sent_clean[:80]}...'")
        if len(suggestions) >= 5:
            break
    return suggestions

# ---------------- Resume-only ATS ----------------
def ats_score_resume_only(resume_text, matched_skills, present_sections):
    skill_score = (len(matched_skills) / len(load_skills())) * 40
    section_score = (len(present_sections) / 6) * 30

    verb_count = sum(resume_text.count(v) for v in ACTION_VERBS)
    action_score = min(verb_count * 5, 20)

    length_score = 10 if len(resume_text.split()) > 250 else 5

    ats = skill_score + section_score + action_score + length_score
    return round(min(ats, 100), 2)

# ---------------- Actionable Suggestions ----------------
def actionable_tips(missing_skills, missing_sections, improvement_suggestions):
    tips = []
    if missing_skills:
        tips.append(f"Add missing skills: {', '.join(missing_skills[:10])}")
    if missing_sections:
        tips.append(f"Add missing sections: {', '.join(missing_sections)}")
    if improvement_suggestions:
        tips.append("Improve weak sentences:")
        tips.extend(improvement_suggestions)
    return tips

# ---------------- Streamlit UI ----------------
st.title("🚀 Resume Checker + ATS ")

uploaded_file = st.file_uploader("Upload Resume (PDF/DOCX)", type=["pdf","docx"])

if uploaded_file:
    resume_text = extract_text(uploaded_file)

    matched_skills, missing_skills = find_skills(resume_text)
    present_sections, missing_sections = structure_feedback(resume_text)
    improvement_suggestions = suggest_sentences(resume_text)

    ats = ats_score_resume_only(resume_text, matched_skills, present_sections)

    tips = actionable_tips(missing_skills, missing_sections, improvement_suggestions)

    st.subheader("📊 ATS Score")
    st.success(f"{ats}%")

    st.subheader("✅ Matched Skills")
    st.write(", ".join(matched_skills))

    st.subheader("⚠️ Missing Skills")
    st.write(", ".join(missing_skills[:10]))

    st.subheader("📑 Present Sections")
    st.write(", ".join(present_sections))

    st.subheader("⚠️ Missing Sections")
    st.write(", ".join(missing_sections))

    st.subheader("💡 Actionable Suggestions")
    for tip in tips:
        st.write(f"- {tip}")
