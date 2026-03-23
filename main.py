import json
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from services.resume_parser import extract_text_from_pdf, extract_text_from_docx, extract_resume_data
from services.skill_matcher import analyze_resume_against_market
from models.user import User, SavedJob, ResumeAnalysis
from models.job import Job
from models.database import engine, Base, get_db
from datetime import datetime, timedelta
from utils.init_db import init_db_data
import os
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from starlette.responses import RedirectResponse

# Create DB tables
Base.metadata.create_all(bind=engine)

# Security Config
SECRET_KEY = "your-secret-key-change-this-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(request: Request, db: Session):
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        user = db.query(User).filter(User.email == email).first()
        return user
    except JWTError:
        return None

app = FastAPI(title="Job Analytics & Resume Matcher API")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
def startup_event():
    try:
        # Create all DB tables if they don't exist
        Base.metadata.create_all(bind=engine)
        # Initialize DB with data if empty
        db = next(get_db())
        init_db_data(db)
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"⚠️ Database init error (non-fatal): {e}")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def generate_chart_data(analysis_results, user_skills):
    salary_counts = {"0-10": 0, "11-20": 0, "21-30": 0, "31+": 0, "Unspecified": 0}
    skill_freq = {}
    
    # Analyze top 20 matches for the charts to remain relevant to the user's focus
    top_matches = analysis_results[:20] if len(analysis_results) > 20 else analysis_results
    
    for job in top_matches:
        lpa_str = job.get("salary_lpa", "")
        if not lpa_str or lpa_str == "None" or lpa_str == "Not Specified":
            salary_counts["Unspecified"] += 1
        else:
            try:
                lpa_val = float(str(lpa_str).replace("LPA", "").strip())
                if lpa_val <= 10: salary_counts["0-10"] += 1
                elif lpa_val <= 20: salary_counts["11-20"] += 1
                elif lpa_val <= 30: salary_counts["21-30"] += 1
                else: salary_counts["31+"] += 1
            except:
                salary_counts["Unspecified"] += 1
                
        for skill in job.get("matched_skills", []) + job.get("missing_skills", []):
            skill_freq[skill] = skill_freq.get(skill, 0) + 1
            
    items = list(skill_freq.items())
    top_skills = sorted(items, key=lambda x: int(x[1]), reverse=True)
    top_subset = top_skills[:6]
    
    radar_labels = []
    radar_market = []
    radar_user = []
    
    user_skills_lower = [s.lower().strip() for s in user_skills]
    
    for item in top_subset:
        skill_name = str(item[0])
        skill_count = int(item[1])
        radar_labels.append(skill_name.capitalize())
        radar_market.append(skill_count)
        if skill_name.lower().strip() in user_skills_lower:
            radar_user.append(skill_count)
        else:
            radar_user.append(0)
    
    return {
        "salary_labels": list(salary_counts.keys()),
        "salary_data": list(salary_counts.values()),
        "radar_labels": radar_labels,
        "radar_market": radar_market,
        "radar_user": radar_user
    }

@app.get("/salary")
def salary_insights(request: Request, db: Session = Depends(get_db)):
    jobs = db.query(Job).all()
    
    role_salaries = {}
    exp_salaries = {"Entry Level": [], "Mid Level": [], "Senior": []}
    
    for job in jobs:
        lpa_str = job.salary_lpa
        if not lpa_str or lpa_str == "None" or lpa_str == "Not Specified":
            continue
            
        try:
            lpa_val = float(str(lpa_str).replace("LPA", "").strip())
            
            # Role aggregation
            role = job.role
            if role not in role_salaries:
                role_salaries[role] = []
            role_salaries[role].append(lpa_val)
            
            # Experience aggregation
            exp = job.experience_level
            if exp in exp_salaries:
                exp_salaries[exp].append(lpa_val)
        except:
            continue
            
    # Calculate averages
    avg_role_salaries = {role: round(sum(sals)/len(sals), 1) for role, sals in role_salaries.items() if sals}
    
    def get_avg(key):
        vals = exp_salaries.get(key, [])
        return round(sum(vals)/len(vals), 1) if vals else 0

    # Sort roles by salary to show top paying ones
    sorted_roles = sorted(avg_role_salaries.items(), key=lambda x: x[1], reverse=True)[:10]
    
    chart_data = {
        "role_labels": [r[0] for r in sorted_roles],
        "role_values": [r[1] for r in sorted_roles],
        "exp_entry": get_avg("Entry Level"),
        "exp_mid": get_avg("Mid Level"),
        "exp_senior": get_avg("Senior")
    }
    
    return templates.TemplateResponse("salary.html", {
        "request": request,
        "chart_data": chart_data,
        "user": get_current_user(request, db)
    })


@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("auth.html", {"request": request, "mode": "login"})

@app.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse("auth.html", {"request": request, "mode": "register"})

@app.post("/register")
async def register(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if user:
        return templates.TemplateResponse("auth.html", {"request": request, "mode": "register", "error": "Email already registered"})
    
    new_user = User(email=email, hashed_password=get_password_hash(password))
    db.add(new_user)
    db.commit()
    return RedirectResponse(url="/login", status_code=303)

@app.post("/login")
async def login(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse("auth.html", {"request": request, "mode": "login", "error": "Invalid email or password"})
    
    access_token = create_access_token(data={"sub": user.email})
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response

@app.get("/logout")
def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie("access_token")
    return response

@app.get("/")
def read_root(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "user": get_current_user(request, db)
    })

@app.get("/dashboard")
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    
    saved_jobs = db.query(SavedJob).filter(SavedJob.user_id == user.id).all()
    past_analyses = db.query(ResumeAnalysis).filter(ResumeAnalysis.user_id == user.id).order_by(ResumeAnalysis.timestamp.desc()).all()
    
    # Calculate stats
    total_analyses = len(past_analyses)
    avg_match = 0.0
    if total_analyses > 0:
        total_scores = sum([float(a.match_percentage) for a in past_analyses])
        avg_match = total_scores / total_analyses
        
    # Prepare trend data for chart
    trend_data = []
    trend_slice = past_analyses[:10]
    for a in reversed(trend_slice):
        trend_data.append({
            "date": a.timestamp.strftime('%b %d'),
            "score": a.match_percentage
        })
        
    # Market Insights: Top Skills
    all_jobs = db.query(Job).all()
    market_skill_freq = {}
    for j in all_jobs:
        if j.required_skills:
            for s in str(j.required_skills).split(","):
                s_clean = s.strip().capitalize()
                if s_clean:
                    market_skill_freq[s_clean] = market_skill_freq.get(s_clean, 0) + 1
    
    market_list = list(market_skill_freq.items())
    sorted_market = sorted(market_list, key=lambda x: int(x[1]), reverse=True)
    top_market_skills = sorted_market[:5]
    
    # Market Insights: Top Paying Roles
    role_salaries = {}
    for job in all_jobs:
        if job.salary_lpa and job.salary_lpa != "None":
            try:
                val = float(str(job.salary_lpa).replace("LPA", "").strip())
                if job.role not in role_salaries: role_salaries[job.role] = []
                role_salaries[job.role].append(val)
            except: continue
    
    roles_summary = [(r, sum(s)/len(s)) for r, s in role_salaries.items()]
    sorted_roles = sorted(roles_summary, key=lambda x: float(x[1]), reverse=True)
    top_paying_roles = sorted_roles[:5]
        
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "saved_jobs": saved_jobs,
        "past_analyses": past_analyses,
        "stats": {
            "total_analyses": total_analyses,
            "avg_match": "{:.1f}".format(avg_match)
        },
        "trend_data": trend_data,
        "market_insights": {
            "top_skills": top_market_skills,
            "top_roles": [{"role": r[0], "salary": round(r[1], 1)} for r in top_paying_roles]
        }
    })

@app.get("/view_analysis/{analysis_id}")
async def view_past_analysis(analysis_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    
    analysis = db.query(ResumeAnalysis).filter(ResumeAnalysis.id == analysis_id, ResumeAnalysis.user_id == user.id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    data = json.loads(analysis.full_data)
    
    return templates.TemplateResponse("results.html", {
        "request": request,
        "filename": data["filename"],
        "extracted_skills": data["extracted_skills"],
        "education": data["education"],
        "experience": data["experience"],
        "personal_info": data["personal_info"],
        "internships": data["internships"],
        "certificates": data["certificates"],
        "projects": data["projects"],
        "analysis": data["analysis"],
        "chart_data": data["chart_data"],
        "current_filters": None,
        "user": user,
        "is_historical": True
    })

@app.post("/save_job/{job_id}")
async def save_job(job_id: str, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return HTTPException(status_code=401, detail="Please login to save jobs")
    
    # Check if already saved
    existing = db.query(SavedJob).filter(SavedJob.user_id == user.id, SavedJob.job_id == job_id).first()
    if existing:
        return {"status": "already_saved"}
    
    new_saved = SavedJob(user_id=user.id, job_id=job_id)
    db.add(new_saved)
    db.commit()
    return {"status": "success"}

@app.post("/remove_job/{job_id}")
async def remove_job(job_id: str, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return HTTPException(status_code=401, detail="Please login")
    
    db.query(SavedJob).filter(SavedJob.user_id == user.id, SavedJob.job_id == job_id).delete()
    db.commit()
    return {"status": "success"}

@app.get("/search")
def search_jobs(request: Request, q: str = "", location: str = "", employment_type: str = "", db: Session = Depends(get_db)):
    query = db.query(Job)
    if q:
        search = f"%{q}%"
        query = query.filter(Job.role.ilike(search) | Job.company.ilike(search) | Job.required_skills.ilike(search))
    if location:
        query = query.filter(Job.location.ilike(f"%{location}%") | Job.remote_type.ilike(f"%{location}%"))
    if employment_type:
        query = query.filter(Job.employment_type == employment_type)
    jobs = query.limit(50).all()
    return templates.TemplateResponse("search.html", {
        "request": request,
        "jobs": jobs,
        "q": q,
        "location": location,
        "employment_type": employment_type,
        "user": get_current_user(request, db)
    })

@app.get("/job/{job_id}")
def job_detail(job_id: str, request: Request, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return templates.TemplateResponse("job_detail.html", {
        "request": request,
        "job": job,
        "user": get_current_user(request, db)
    })

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
        personal_info = resume_data.get("personal_info", {"email": "None", "phone": "None"})
        internships = resume_data.get("internships", False)
        certificates = resume_data.get("certificates", False)
        projects = resume_data.get("projects", False)
        
        analysis_results = analyze_resume_against_market(resume_data, db)
        chart_data = generate_chart_data(analysis_results, skills)
        
        # Save analysis if user is logged in
        user = get_current_user(request, db)
        if user and analysis_results:
            first_match = analysis_results[0]
            m_score = first_match.get("match_score", 0)
            m_skills = first_match.get("missing_skills", [])
            
            # Prepare full data for reconstruction
            full_results = {
                "filename": file.filename,
                "extracted_skills": skills,
                "education": education,
                "experience": experience,
                "personal_info": personal_info,
                "internships": internships,
                "certificates": certificates,
                "projects": projects,
                "analysis": analysis_results,
                "chart_data": chart_data
            }
            
            new_analysis = ResumeAnalysis(
                user_id=user.id,
                filename=file.filename,
                match_percentage=float(m_score),
                top_skills=",".join(skills[:10]),
                missing_skills=",".join(m_skills),
                full_data=json.dumps(full_results)
            )
            db.add(new_analysis)
            db.commit()
        
        return templates.TemplateResponse("results.html", {
            "request": request,
            "filename": file.filename,
            "extracted_skills": skills,
            "education": education,
            "experience": experience,
            "personal_info": personal_info,
            "internships": internships,
            "certificates": certificates,
            "projects": projects,
            "analysis": analysis_results,
            "chart_data": chart_data,
            "current_filters": None,
            "user": get_current_user(request, db)
        })
    except Exception as e:
        return templates.TemplateResponse("index.html", {
            "request": request, 
            "error": str(e),
            "user": get_current_user(request, db)
        })

@app.post("/filter_results")
async def filter_results(
    request: Request,
    filename: str = Form(...),
    extracted_skills: str = Form(...),
    education: str = Form(...),
    experience: str = Form(...),
    email: str = Form("None"),
    phone: str = Form("None"),
    internships: str = Form("False"),
    certificates: str = Form("False"),
    projects: str = Form("False"),
    search_query: str = Form(""),
    employment_type: str = Form("Any"),
    location: str = Form("Any"),
    date_posted: str = Form("Any"),
    db: Session = Depends(get_db)
):
    try:
        skills = [s.strip() for s in extracted_skills.split(",")] if extracted_skills else []
        
        filters = {
            "search_query": search_query,
            "employment_type": employment_type,
            "location": location,
            "date_posted": date_posted
        }
        
        # Create a full dict to pass to the matcher
        resume_data = {
            "skills": skills,
            "experience": experience,
            "education": education,
            "internships": internships == "True",
            "certificates": certificates == "True",
            "projects": projects == "True"
        }
        
        # Analyze against market with filters
        analysis_results = analyze_resume_against_market(resume_data, db, filters=filters)
        chart_data = generate_chart_data(analysis_results, skills)
        
        # Save analysis if user is logged in
        user = get_current_user(request, db)
        if user and analysis_results:
            first_match = analysis_results[0]
            m_score = first_match.get("match_score", 0)
            m_skills = first_match.get("missing_skills", [])
            
            # Prepare full data for reconstruction
            full_results = {
                "filename": filename,
                "extracted_skills": skills,
                "education": education,
                "experience": experience,
                "personal_info": {"email": email, "phone": phone},
                "internships": internships == "True",
                "certificates": certificates == "True",
                "projects": projects == "True",
                "analysis": analysis_results,
                "chart_data": chart_data
            }
            
            new_analysis = ResumeAnalysis(
                user_id=user.id,
                filename=filename,
                match_percentage=float(m_score),
                top_skills=",".join(skills[:10]),
                missing_skills=",".join(m_skills),
                full_data=json.dumps(full_results)
            )
            db.add(new_analysis)
            db.commit()
        
        return templates.TemplateResponse("results.html", {
            "request": request,
            "filename": filename,
            "extracted_skills": skills,
            "education": education,
            "experience": experience,
            "personal_info": {"email": email, "phone": phone},
            "internships": internships == "True",
            "certificates": certificates == "True",
            "projects": projects == "True",
            "analysis": analysis_results,
            "current_filters": filters,
            "chart_data": chart_data,
            "user": get_current_user(request, db)
        })
    except Exception as e:
        return templates.TemplateResponse("index.html", {
            "request": request, 
            "error": str(e),
            "user": get_current_user(request, db)
        })
