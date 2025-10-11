import os
import streamlit as st
from dotenv import load_dotenv
from PIL import Image
import google.generativeai as genai
from pdf2image import convert_from_path
import pytesseract
import pdfplumber

# -------------------------------------------
# Load environment variables
# -------------------------------------------
load_dotenv()

# Configure Google Gemini AI
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# -------------------------------------------
# ✅ Extract text from PDF (text or scanned)
# -------------------------------------------
def extract_text_from_pdf(pdf_path):
    text = ""

    # Try direct extraction (works for normal PDFs)
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

        # If text found, return it
        if text.strip():
            print(" Text extracted")
            return text.strip()

    except Exception as e:
        print(f"⚠️ Direct text extraction failed: {e}")

    # Fallback to OCR for image-based PDFs
    print("⚙️ Falling back to OCR for scanned PDF...")
    try:
        images = convert_from_path(pdf_path)
        for i, image in enumerate(images):
            gray = image.convert("L")  # grayscale for better OCR
            page_text = pytesseract.image_to_string(gray)
            text += f"\n\n--- Page {i+1} ---\n{page_text}"
        print("✅ Text extracted using OCR.")
    except Exception as e:
        print(f"❌ OCR extraction failed: {e}")

    return text.strip()

# -------------------------------------------
# ✅ Extract text from images (JPG, PNG, etc.)
# -------------------------------------------
def extract_text_from_image(image_file):
    try:
        image = Image.open(image_file)
        gray = image.convert("L")
        text = pytesseract.image_to_string(gray)
        print("Text extracted from image using OCR.")
        return text.strip()
    except Exception as e:
        print(f"❌ Image OCR failed: {e}")
        return ""

# -------------------------------------------
# ✅ Analyze Resume with Gemini AI
# -------------------------------------------
def analyze_resume(resume_text, job_description=None):
    if not resume_text:
        return "❌ No text could be extracted from the file."

    model = genai.GenerativeModel("models/gemini-2.5-pro")

    base_prompt = f"""
    You are an experienced HR professional with technical expertise in fields like
    Data Science, Data Analysis, DevOps, Machine Learning, Prompt Engineering,
    AI Engineering, Full Stack Web Development, Big Data Engineering,
    Marketing Analysis, Human Resource Management, or Software Development.

    Review the following resume and provide:
    - Strengths and weaknesses
    - Skills already present
    - Skills to improve
    - Recommended courses/certifications
    - Overall job role alignment

    Resume:
    {resume_text}
    """

    if job_description:
        base_prompt += f"""
        Additionally, compare this resume with the following Job Description:

        Job Description:
        {job_description}

        Mention how well the applicant matches the role and areas of improvement.
        """

    try:
        response = model.generate_content(base_prompt)
        return response.text.strip()
    except Exception as e:
        return f"❌ Gemini AI analysis failed: {e}"

# -------------------------------------------
# ✅ Streamlit App Layout
# -------------------------------------------
st.set_page_config(page_title="AI Resume Analyzer", layout="wide")

# Title
st.title(" AI Resume & Image Analyzer")
st.write("Upload your resume as a **PDF** or **Image (JPG/PNG)** — text or scanned, all supported!")

col1, col2 = st.columns(2)
with col1:
    uploaded_file = st.file_uploader(
        "Upload your resume (PDF or Image)",
        type=["pdf", "jpg", "jpeg", "png"]
    )
with col2:
    job_description = st.text_area(
        "Enter Job Description (optional):",
        placeholder="Paste the job description here..."
    )

# Process file
if uploaded_file is not None:
    st.success(" File uploaded successfully!")

    file_ext = uploaded_file.name.lower().split(".")[-1]

    # Extract text
    with st.spinner("Extracting text from your file..."):
        resume_text = ""
        if file_ext == "pdf":
            with open("uploaded_resume.pdf", "wb") as f:
                f.write(uploaded_file.getbuffer())
            resume_text = extract_text_from_pdf("uploaded_resume.pdf")
        elif file_ext in ["jpg", "jpeg", "png"]:
            resume_text = extract_text_from_image(uploaded_file)

    # Show preview
    if resume_text:
        st.text_area(" Extracted Resume Text (Preview):", resume_text[:1500], height=250)
    else:
        st.error(" Could not extract text from the file. Try uploading a clearer image or PDF.")

    # Analyze
    if st.button(" Analyze Resume"):
        with st.spinner("Analyzing your resume with Gemini AI..."):
            analysis = analyze_resume(resume_text, job_description)
            st.success(" Analysis complete!")
            st.write(analysis)
else:
    st.warning("Please upload a resume file (PDF or image) to begin.")

