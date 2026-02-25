from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from services.resume_parser import extract_text_from_pdf, extract_text_from_docx, extract_resume_data
from services.skill_matcher import analyze_resume_against_market
from models.database import engine, Base, get_db
from models.job import Job
from utils.init_db import init_db_data

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Job Analytics & Resume Matcher API")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
def startup_event():
    # Initialize DB with mock data if empty
    db = next(get_db())
    init_db_data(db)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/trends")
def get_trends(db: Session = Depends(get_db)):
    jobs = db.query(Job).order_by(Job.trend_score.desc()).all()
    # Return as list of dicts
    return [
        {
            "id": job.id,
            "role": job.role,
            "company": job.company,
            "required_skills": job.required_skills.split(","),
            "trend_score": job.trend_score
        } for job in jobs
    ]

@app.post("/upload_resume")
async def upload_resume_ui(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(('.pdf', '.docx')):
        return templates.TemplateResponse("index.html", {"request": request, "error": "Invalid file type. Only PDF and DOCX are supported."})
    
    try:
        file_bytes = await file.read()
        if file.filename.endswith('.pdf'):
            text = extract_text_from_pdf(file_bytes)
        else:
            text = extract_text_from_docx(file_bytes)
            
        if not text.strip():
            return templates.TemplateResponse("index.html", {"request": request, "error": "Could not extract text from the provided file."})
            
        resume_data = extract_resume_data(text)
        skills = resume_data["skills"]
        education = resume_data["education"]
        experience = resume_data["experience"]
        
        # Analyze against market
        analysis_results = analyze_resume_against_market(skills, db)
        
        return templates.TemplateResponse("results.html", {
            "request": request,
            "filename": file.filename,
            "extracted_skills": skills,
            "education": education,
            "experience": experience,
            "analysis": analysis_results
        })
    except Exception as e:
        return templates.TemplateResponse("index.html", {"request": request, "error": str(e)})
