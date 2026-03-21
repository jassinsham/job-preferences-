import fitz  # PyMuPDF
import docx2txt
import spacy
import re
import io

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    import spacy.cli
    spacy.cli.download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

def extract_text_from_pdf(file_bytes: bytes) -> str:
    text = ""
    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

def extract_text_from_docx(file_bytes: bytes) -> str:
    text = docx2txt.process(io.BytesIO(file_bytes))
    return text

def extract_resume_data(text: str) -> dict:
    doc = nlp(text)
    
    # Common tech skills dictionary (simplified for demo)
    tech_skills = {
        "python", "java", "javascript", "react", "node.js", "sql", "aws", "docker",
        "kubernetes", "machine learning", "data analysis", "html", "css", "c++",
        "c#", "ruby", "php", "go", "fastapi", "flask", "django", "spring boot",
        "nlp", "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy", "git",
        "agile", "scrum", "leadership", "communication"
    }
    
    found_skills = set()
    text_lower = text.lower()
    
    for skill in tech_skills:
        # Avoid partial word matches using regex word boundaries
        if re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
            found_skills.add(skill)

    # Simple heuristic for Education
    education_level = "Unknown"
    if re.search(r'\b(ph\.?d\.?|doctorate)\b', text_lower):
        education_level = "Ph.D."
    elif re.search(r'\b(master\'?s?|ms|m\.?s\.?|mba)\b', text_lower):
        education_level = "Master's"
    elif re.search(r'\b(bachelor\'?s?|bs|b\.?s\.?|ba|b\.?a\.?)\b', text_lower):
        education_level = "Bachelor's"
        
    # Simple heuristic for Experience Level
    experience_level = "Entry Level" # Default
    # Look for patterns like "5 years of experience", "5+ years", etc.
    exp_matches = re.findall(r'(\d+)\+?\s*years?', text_lower)
    
    if exp_matches:
        max_years = max([int(y) for y in exp_matches if int(y) < 50]) # filter out noise
        if max_years >= 5:
            experience_level = "Senior"
        elif max_years >= 2:
            experience_level = "Mid Level"
            
    # Extract Email
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    email = email_match.group(0) if email_match else "None"

    # Extract Phone Number (Common formats)
    phone_match = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
    phone = phone_match.group(0) if phone_match else "None"

    # Extract Internships (Simple heuristic)
    has_internship = False
    if re.search(r'\b(intern|internship)\b', text_lower):
        has_internship = True

    # Extract Certificates (Simple heuristic)
    has_certificate = False
    if re.search(r'\b(certif|coursera|udemy|edx)\b', text_lower):
        has_certificate = True

    # Extract Projects (Simple heuristic)
    has_project = False
    if re.search(r'\b(project|github|developed|created)\b', text_lower):
        has_project = True

    return {
        "personal_info": {"email": email, "phone": phone},
        "skills": list(found_skills),
        "education": education_level,
        "experience": experience_level,
        "internships": has_internship,
        "certificates": has_certificate,
        "projects": has_project
    }
