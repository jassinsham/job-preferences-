from sqlalchemy.orm import Session
from models.job import Job

def calculate_match(resume_skills: list[str], job_skills: list[str]) -> dict:
    """
    Compares the skills extracted from the resume against the required skills for a job.
    Returns the match percentage and missing skills.
    """
    resume_skills_set = set(s.lower() for s in resume_skills)
    job_skills_set = set(s.lower() for s in job_skills)
    
    if not job_skills_set:
        return {"match_percentage": 0, "matched_skills": [], "missing_skills": []}

    matched_skills = list(resume_skills_set.intersection(job_skills_set))
    missing_skills = list(job_skills_set.difference(resume_skills_set))
    
    match_percentage = round((len(matched_skills) / len(job_skills_set)) * 100, 2)
    
    return {
        "match_percentage": match_percentage,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
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
        "trend_score": 95
    },
    {
        "id": "job_002",
        "role": "Backend Engineer",
        "company": "DataFlow Systems",
        "required_skills": ["python", "fastapi", "sql", "docker", "aws", "git"],
        "trend_score": 92
    },
    {
        "id": "job_003",
        "role": "Full Stack Developer",
        "company": "StartupX",
        "required_skills": ["react", "node.js", "javascript", "sql", "aws", "docker"],
        "trend_score": 88
    },
    {
        "id": "job_004",
        "role": "Machine Learning Engineer",
        "company": "AI Solutions",
        "required_skills": ["python", "machine learning", "pytorch", "tensorflow", "scikit-learn", "pandas", "sql"],
        "trend_score": 98
    }
]

def analyze_resume_against_market(resume_skills: list[str], db: Session) -> list[dict]:
    results = []
    
    # Query all jobs from DB instead of using MOCK_JOB_DATA
    jobs = db.query(Job).all()
    
    for job in jobs:
        # Convert comma separated string to list
        required_skills = [s.strip() for s in job.required_skills.split(",")] if job.required_skills else []
        
        match_info = calculate_match(resume_skills, required_skills)
        results.append({
            "job_id": job.id,
            "role": job.role,
            "company": job.company,
            "trend_score": job.trend_score,
            **match_info
        })
    # Sort by best match
    results.sort(key=lambda x: x["match_percentage"], reverse=True)
    return results
