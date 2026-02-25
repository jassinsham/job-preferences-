from sqlalchemy.orm import Session
from models.job import Job
from services.skill_matcher import MOCK_JOB_DATA

def init_db_data(db: Session):
    # Check if we already have jobs
    if db.query(Job).first():
        return
    
    # If empty, populate with MOCK_JOB_DATA
    for job_data in MOCK_JOB_DATA:
        job = Job(
            id=job_data["id"],
            role=job_data["role"],
            company=job_data["company"],
            required_skills=",".join(job_data["required_skills"]),
            trend_score=job_data["trend_score"]
        )
        db.add(job)
    
    db.commit()
