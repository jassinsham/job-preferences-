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

def extract_skills(text: str) -> list[str]:
    # Basic skill extraction logic using NER and predefined lists/patterns
    # For a production app, we would use a more comprehensive skill taxonomy or custom NER model.
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
    
    # Simple keyword matching
    text_lower = text.lower()
    for skill in tech_skills:
        # Avoid partial word matches using regex word boundaries
        if re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
            found_skills.add(skill)

    # Adding entities found by Spacy that might be skills (ORG, PRODUCT, GPE sometimes misclassified)
    # This is rudimentary, typically a dedicated NER for skills is better.
    return list(found_skills)
