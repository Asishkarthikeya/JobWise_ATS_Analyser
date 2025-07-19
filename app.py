import os
os.environ["XDG_CONFIG_HOME"] = "/tmp"

import asyncio
try:
    asyncio.get_running_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())
import streamlit as st
import requests
from PyPDF2 import PdfReader
from docx import Document
import hashlib
import matplotlib.pyplot as plt
import re
from io import BytesIO
from fpdf import FPDF
import time

st.set_page_config(page_title="JobWise ATS Analyzer", layout="wide", initial_sidebar_state="expanded")

# ----- Theme & Static Logo -----
st.markdown("""
    <style>
        body { background-color: #0e1117; color: white; }
        .stButton>button { background-color: #0066cc; color: white; font-weight: bold; }
        .block-container {padding-top: 2rem;}
        .typing-effect span {
            display: inline-block;
            animation: blink 1s infinite;
        }
        @keyframes blink {
            0% { opacity: 0; }
            50% { opacity: 1; }
            100% { opacity: 0; }
        }
    </style>
""", unsafe_allow_html=True)

st.image("Jobwise_Logo.png", width=140)

st.markdown("""
    <div style='text-align: center;'>
        <h1 style='color:#00bfff;'>JobWise</h1>
        <p style='font-size:18px;'>Your AI guide to get a job <span class='typing-effect'>💡</span></p>
    </div>
""", unsafe_allow_html=True)

API_KEY = os.getenv("AIzaSyBoB1UU5C5tdReHUVpZS2ohGn-A2V2z-3Y")  # Replace with your actual Gemini API key

def extract_text_from_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    return "".join(page.extract_text() or "" for page in reader.pages)

def extract_text_from_docx(docx_file):
    doc = Document(docx_file)
    return "\n".join(para.text for para in doc.paragraphs)

def analyze_documents(resume_text, job_description):
    prompt = f"""Please analyze the following resume in the context of the job description provided. Provide:
    - Match percentage
    - Missing keywords (hard + soft skills)
    - Final evaluation in 3 lines
    - 3-4 actionable improvement points
    Job Description: {job_description}
    Resume: {resume_text}"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={API_KEY}"
    return requests.post(url, json={"contents":[{"role":"user","parts":[{"text":prompt}]}]}).json()

def rephrase_text(text):
    prompt = f"""Rephrase the following resume content with ATS-optimized phrasing and measurable outcomes:\n{text}"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={API_KEY}"
    return requests.post(url, json={"contents":[{"role":"user","parts":[{"text":prompt}]}]}).json()

def skill_gap_analysis(resume_text, job_description):
    prompt = f"""Compare resume and job description. Return:
    - Matched hard and soft skills
    - Missing hard and soft skills
    - Suggestions to close the skill gaps
    Resume: {resume_text}
    Job Description: {job_description}"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={API_KEY}"
    return requests.post(url, json={"contents":[{"role":"user","parts":[{"text":prompt}]}]}).json()

def generate_pdf(content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.set_auto_page_break(auto=True, margin=15)
    for line in content.splitlines():
        pdf.multi_cell(0, 10, line)
    return pdf.output(dest='S').encode('latin1')  # Return as byte string



# -------- Sidebar Navigation --------
st.sidebar.title("Navigation")
page = st.sidebar.radio("Select Tool", ["📄 Resume Analyzer", "✨ Magic Rephrase", "📁 ATS Templates", "📊 Skill Gap Analyzer"])

# -------- Resume Analyzer Tab --------
if page == "📄 Resume Analyzer":
    st.header("📄 ATS Resume Analyzer")
    jd = st.text_area("Job Description")
    rc = st.file_uploader("Upload Resume", type=["pdf", "docx"])
    if rc and jd and st.button("🔍 Analyze Resume"):
        rt = extract_text_from_pdf(rc) if rc.name.lower().endswith("pdf") else extract_text_from_docx(rc)
        analysis = analyze_documents(rt, jd)
        candidates = analysis.get("candidates", [])
        if not candidates:
            st.error("No analysis response received.")
        else:
            parts = candidates[0].get("content", {}).get("parts", [])
            full_feedback = ""
            for p in parts:
                text = p.get("text", "")
                st.markdown(text)
                full_feedback += text + "\n"
                if "match percentage" in text.lower():
                    try:
                        match = re.search(r"(\d+)%", text)
                        if match:
                            perc = int(match.group(1))
                            st.progress(perc)
                            fig, ax = plt.subplots(figsize=(2, 2))
                            ax.pie([perc, 100 - perc], labels=['Matched', 'Unmatched'],
                                   autopct='%1.1f%%', startangle=90, colors=["#00bfff", "#333"])
                            ax.axis('equal')
                            st.pyplot(fig)
                    except Exception as e:
                        st.warning(f"Graph error: {e}")
            st.download_button("📄 Download Feedback as PDF",data=generate_pdf(full_feedback), file_name="resume_feedback.pdf")


# -------- Magic Rephrase Tab --------
elif page == "✨ Magic Rephrase":
    st.header("🔮 Magic Rephrase")
    txt = st.text_area("Text to rephrase")
    if txt and st.button("Rephrase"):
        resp = rephrase_text(txt)
        parts = resp.get("candidates", [])[0].get("content", {}).get("parts", [])
        for p in parts:
            st.success(p.get("text", ""))

# -------- ATS Templates Tab --------
elif page == "📁 ATS Templates":
    st.header("📁 ATS Templates")
    st.markdown("Choose from these ATS-friendly resume templates:")
    templates = {
        "Modern Minimal": "https://docs.google.com/document/d/1NWFIz-EZ1ZztZSdXfrrcdffSzG-uermd/edit",
        "Elegant Blue": "https://docs.google.com/document/d/1xO7hvK-RQSb0mjXRn24ri3AiDrXx6qt8/edit",
        "Classic Chronological": "https://docs.google.com/document/d/1fAukvT0lWXns3VexbZjwXyCAZGw2YptO/edit"
    }
    for name, url in templates.items():
        st.markdown(f"**[{name}]({url})**")

# -------- Skill Gap Analyzer Tab --------
elif page == "📊 Skill Gap Analyzer":
    st.header("📊 Skill Gap Analyzer")
    jd2 = st.text_area("Job Description", key="jd2")
    rf2 = st.file_uploader("Upload resume", type=["pdf", "docx"], key="rf2")
    if rf2 and jd2 and st.button("Analyze Skill Gaps"):
        rt = extract_text_from_pdf(rf2) if rf2.name.lower().endswith("pdf") else extract_text_from_docx(rf2)
        result = skill_gap_analysis(rt, jd2)
        for candidate in result.get("candidates", []):
            for part in candidate.get("content", {}).get("parts", []):
                st.markdown(part.get("text", ""))
