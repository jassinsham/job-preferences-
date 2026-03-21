from sqlalchemy.orm import Session
from models.job import Job

def calculate_match(resume_data: dict, job: Job) -> dict:
    """
    Compares the full resume data against the job requirements.
    Weights: 
      - Skills Match: 50%
      - Experience Level Match: 15%
      - Education Match: 10%
      - Internships Present: 5%
      - Certificates Present: 10%
      - Projects Present: 10%
    """
    
    # 1. Skills (50%)
    resume_skills_set = set(s.lower() for s in resume_data.get("skills", []))
    job_skills_list = [s.strip() for s in job.required_skills.split(",")] if job.required_skills else []
    job_skills_set = set(s.lower() for s in job_skills_list)
    
    if not job_skills_set:
        skill_score = 50.0  # Perfect score if no skills required
        matched_skills = []
        missing_skills = []
    else:
        matched_skills = list(resume_skills_set.intersection(job_skills_set))
        missing_skills = list(job_skills_set.difference(resume_skills_set))
        skill_score = (len(matched_skills) / len(job_skills_set)) * 50.0

    # 2. Experience Level (15%)
    exp_weights = {"Entry Level": 1, "Mid Level": 2, "Senior": 3}
    res_exp_val = exp_weights.get(resume_data.get("experience"), 1)
    job_exp_val = exp_weights.get(job.experience_level, 1)
    
    if res_exp_val >= job_exp_val:
        exp_score = 15.0  # Meets or exceeds
    elif job_exp_val - res_exp_val == 1:
        exp_score = 7.5   # One level below
    else:
        exp_score = 0.0   # Two levels below
        
    # 3. Education Match (10%)
    edu_weights = {"High School": 1, "Bachelor's": 2, "Master's": 3, "Ph.D.": 4, "Not Specified": 0}
    res_edu_val = edu_weights.get(resume_data.get("education"), 0)
    job_edu_val = edu_weights.get(job.education, 0)
    
    if res_edu_val >= job_edu_val or job_edu_val == 0:
        edu_score = 10.0
    else:
        edu_score = 5.0 # Give partial credit

    # 4. Internships Present (5%)
    intern_score = 5.0 if resume_data.get("internships", False) else 0.0
    
    # 5. Certificates Present (10%)
    cert_score = 10.0 if resume_data.get("certificates", False) else 0.0
    
    # 6. Projects Present (10%)
    proj_score = 10.0 if resume_data.get("projects", False) else 0.0

    match_percentage = round(skill_score + exp_score + edu_score + intern_score + cert_score + proj_score, 1)

    return {
        "match_percentage": match_percentage,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "sub_scores": {
            "skills": round(skill_score, 1),
            "experience": round(exp_score, 1),
            "education": round(edu_score, 1),
            "internships": round(intern_score, 1),
            "certificates": round(cert_score, 1),
            "projects": round(proj_score, 1)
        },
        "recommendations": generate_recommendations(missing_skills)
    }

def generate_recommendations(missing_skills: list[str]) -> list[str]:
    # Simple mock recommendations
    recommendations = []
    for skill in missing_skills:
        recommendations.append(f"Consider taking a fast-track course or building a project in {skill.capitalize()}.")
    return recommendations

# Mock Job Data representing "Social Media Job Market Trends"
# We keep this for the initial database population in utils/init_db.py
MOCK_JOB_DATA = [
    {
        "id": "job_001",
        "role": "Frontend Developer",
        "company": "Tech Innovators",
        "required_skills": ["react", "javascript", "html", "css", "git", "agile"],
        "experience_level": "Entry Level",
        "education": "Bachelor's",
        "trend_score": 95
    },
    {
        "id": "job_002",
        "role": "Backend Engineer",
        "company": "DataFlow Systems",
        "required_skills": ["python", "fastapi", "sql", "docker", "aws", "git"],
        "experience_level": "Mid Level",
        "education": "Bachelor's",
        "trend_score": 92
    },
    {
        "id": "job_003",
        "role": "Full Stack Developer",
        "company": "StartupX",
        "required_skills": ["react", "node.js", "javascript", "sql", "aws", "docker"],
        "experience_level": "Mid Level",
        "education": "Bachelor's",
        "trend_score": 88
    },
    {
        "id": "job_004",
        "role": "Machine Learning Engineer",
        "company": "AI Solutions",
        "required_skills": ["python", "machine learning", "pytorch", "tensorflow", "scikit-learn", "pandas", "sql"],
        "experience_level": "Senior",
        "education": "Master's",
        "trend_score": 98
    },
    {
        "id": "job_005",
        "role": "DevOps Engineer",
        "company": "CloudScape",
        "required_skills": ["aws", "docker", "kubernetes", "python", "agile", "sql"],
        "experience_level": "Senior",
        "education": "Bachelor's",
        "trend_score": 94
    },
    {
        "id": "job_006",
        "role": "Data Analyst",
        "company": "Metrics Corp",
        "required_skills": ["sql", "python", "pandas", "data analysis", "communication"],
        "experience_level": "Entry Level",
        "education": "Bachelor's",
        "trend_score": 85
    },
    {
        "id": "job_007",
        "role": "iOS Developer",
        "company": "MobileFirst",
        "required_skills": ["c++", "ruby", "git", "agile"],
        "experience_level": "Mid Level",
        "education": "Bachelor's",
        "trend_score": 81
    },
    {
        "id": "job_008",
        "role": "Backend Python Developer",
        "company": "FinTech Secure",
        "required_skills": ["python", "django", "sql", "fastapi", "kubernetes"],
        "experience_level": "Mid Level",
        "education": "Bachelor's",
        "trend_score": 90
    },
    {
        "id": "job_009",
        "role": "Data Scientist",
        "company": "Predictive Alpha",
        "required_skills": ["python", "machine learning", "scikit-learn", "sql", "aws", "pandas"],
        "experience_level": "Senior",
        "education": "Ph.D.",
        "trend_score": 96
    },
    {
        "id": "job_010",
        "role": "Junior Web Developer",
        "company": "Creative Agency",
        "required_skills": ["html", "css", "javascript", "react"],
        "experience_level": "Entry Level",
        "education": "High School",
        "trend_score": 89
    },
    {
        "id": "job_011",
        "role": "Lead Architect",
        "company": "Enterprise Systems",
        "required_skills": ["java", "spring boot", "aws", "docker", "kubernetes", "leadership"],
        "experience_level": "Senior",
        "education": "Master's",
        "trend_score": 91
    },
    {
        "id": "job_012",
        "role": "Site Reliability Engineer",
        "company": "Global Tech",
        "required_skills": ["python", "go", "aws", "kubernetes", "docker"],
        "experience_level": "Mid Level",
        "education": "Bachelor's",
        "trend_score": 93
    },
    {
        "id": "job_013",
        "role": "Software Engineer, New Grad",
        "company": "Social Network Inc",
        "required_skills": ["c++", "java", "python", "sql", "git"],
        "experience_level": "Entry Level",
        "education": "Bachelor's",
        "trend_score": 87
    },
    {
        "id": "job_014",
        "role": "Senior PHP Developer",
        "company": "Legacy Web Services",
        "required_skills": ["php", "javascript", "html", "css", "sql", "leadership"],
        "experience_level": "Senior",
        "education": "Bachelor's",
        "trend_score": 75
    },
    {
        "id": "job_015",
        "role": "NLP Researcher",
        "company": "AI Labs",
        "required_skills": ["python", "nlp", "tensorflow", "pytorch", "machine learning"],
        "experience_level": "Senior",
        "education": "Ph.D.",
        "trend_score": 99
    },
    {
        "id": "job_016",
        "role": "Cybersecurity Analyst",
        "company": "SecureNet",
        "required_skills": ["python", "sql", "aws", "docker", "communication"],
        "experience_level": "Mid Level",
        "education": "Bachelor's",
        "trend_score": 93
    },
    {
        "id": "job_017",
        "role": "UI/UX Developer",
        "company": "DesignHub",
        "required_skills": ["html", "css", "javascript", "communication", "agile"],
        "experience_level": "Entry Level",
        "education": "Bachelor's",
        "trend_score": 88
    },
    {
        "id": "job_018",
        "role": "Product Manager",
        "company": "Tech Ventures",
        "required_skills": ["agile", "scrum", "leadership", "communication", "data analysis"],
        "experience_level": "Mid Level",
        "education": "Bachelor's",
        "trend_score": 95
    },
    {
        "id": "job_019",
        "role": "QA Automation Engineer",
        "company": "Quality First",
        "required_skills": ["python", "java", "javascript", "sql", "agile"],
        "experience_level": "Mid Level",
        "education": "Bachelor's",
        "trend_score": 87
    },
    {
        "id": "job_020",
        "role": "Blockchain Developer",
        "company": "Crypto Solutions",
        "required_skills": ["go", "c++", "javascript", "node.js"],
        "experience_level": "Senior",
        "education": "Master's",
        "trend_score": 91
    },
    {
        "id": "job_021",
        "role": "Game Developer",
        "company": "Pixel Studios",
        "required_skills": ["c#", "c++", "agile"],
        "experience_level": "Mid Level",
        "education": "Bachelor's",
        "trend_score": 86
    },
    {
        "id": "job_022",
        "role": "Embedded Systems Engineer",
        "company": "Hardware Tech",
        "required_skills": ["c++", "python", "agile"],
        "experience_level": "Mid Level",
        "education": "Bachelor's",
        "trend_score": 82
    },
    {
        "id": "job_023",
        "role": "Cloud Architect",
        "company": "SkyNet Systems",
        "required_skills": ["aws", "docker", "kubernetes", "python", "leadership"],
        "experience_level": "Senior",
        "education": "Master's",
        "trend_score": 97
    },
    {
        "id": "job_024",
        "role": "Database Administrator",
        "company": "Data Fortress",
        "required_skills": ["sql", "aws", "python", "agile"],
        "experience_level": "Mid Level",
        "education": "Bachelor's",
        "trend_score": 85
    },
    {
        "id": "job_025",
        "role": "Network Engineer",
        "company": "Connect IT",
        "required_skills": ["aws", "python", "communication"],
        "experience_level": "Mid Level",
        "education": "Bachelor's",
        "trend_score": 83
    },
    {
        "id": "job_026",
        "role": "Marketing Analytics Manager",
        "company": "Growth Engine",
        "required_skills": ["data analysis", "sql", "python", "pandas", "leadership"],
        "experience_level": "Senior",
        "education": "Master's",
        "trend_score": 89
    },
    {
        "id": "job_027",
        "role": "Scrum Master",
        "company": "Agile Dynamics",
        "required_skills": ["agile", "scrum", "leadership", "communication"],
        "experience_level": "Mid Level",
        "education": "Bachelor's",
        "trend_score": 88
    },
    {
        "id": "job_028",
        "role": "Technical Writer",
        "company": "DocuSignage",
        "required_skills": ["html", "css", "communication", "git"],
        "experience_level": "Entry Level",
        "education": "Bachelor's",
        "trend_score": 79
    },
    {
        "id": "job_029",
        "role": "Systems Administrator",
        "company": "IT Core",
        "required_skills": ["python", "aws", "docker", "sql"],
        "experience_level": "Mid Level",
        "education": "Bachelor's",
        "trend_score": 84
    },
    {
        "id": "job_030",
        "role": "Full Stack Python Developer",
        "company": "Web Solutions",
        "required_skills": ["python", "django", "javascript", "react", "sql", "html", "css"],
        "experience_level": "Mid Level",
        "education": "Bachelor's",
        "trend_score": 94
    }
]

def analyze_resume_against_market(resume_data: dict, db: Session, filters: dict = None) -> list[dict]:
    results = []
    
    query = db.query(Job)
    
    if filters:
        if filters.get("employment_type") and filters["employment_type"] != "Any":
            query = query.filter(Job.employment_type == filters["employment_type"])
            
        if filters.get("location") and filters["location"] != "Any":
            if filters["location"] == "Remote":
                query = query.filter(Job.remote_type.ilike("%remote%"))
            elif filters["location"] == "Hybrid":
                query = query.filter(Job.remote_type.ilike("%hybrid%"))
            elif filters["location"] == "On-site":
                query = query.filter(~Job.remote_type.ilike("%remote%"), ~Job.remote_type.ilike("%hybrid%"))
                
        if filters.get("date_posted") and filters["date_posted"] != "Any":
            if filters["date_posted"] == "Past 24 Hours":
                query = query.filter(Job.posted_days_ago <= 1)
            elif filters["date_posted"] == "Past Week":
                query = query.filter(Job.posted_days_ago <= 7)
                
        if filters.get("search_query"):
            search = f"%{filters['search_query']}%"
            # Search in role or company
            query = query.filter(Job.role.ilike(search) | Job.company.ilike(search))
    
    jobs = query.all()
    
    for job in jobs:
        match_info = calculate_match(resume_data, job)
        results.append({
            "job_id": job.id,
            "role": job.role,
            "company": job.company,
            "location": job.location,
            "employment_type": job.employment_type,
            "experience_level": job.experience_level,
            "education": job.education,
            "salary_lpa": job.salary_lpa,
            "phone_number": job.phone_number,
            "trend_score": job.trend_score,
            **match_info
        })
    # Sort by best match
    results.sort(key=lambda x: x["match_percentage"], reverse=True)
    return results
