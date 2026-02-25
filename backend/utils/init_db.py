from sqlalchemy.orm import Session
from models.job import Job
from services.skill_matcher import MOCK_JOB_DATA
import os

def init_db_data(db: Session):
    # Check if we already have jobs
    if db.query(Job).first():
        return
        
    csv_path = os.path.join(os.path.dirname(__file__), "..", "..", "linkedin_jobs_dataset_500 (1).csv")
    
    if os.path.exists(csv_path):
        import csv
        with open(csv_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            # Headers: Job_ID,Job_Title,Company,Location,Experience_Level,Employment_Type,Skills,Industry,Salary_LPA,Posted_Days_Ago
            for row in reader:
                # Derive a trend score inversely related to Posted_Days_Ago
                # Assumes max days is around 30, scale to 70-100
                days_ago = int(row.get('Posted_Days_Ago', 0))
                trend_score = max(70, 100 - days_ago)
                
                # Sanitize experience level strings
                exp_level = row.get("Experience_Level", "Entry Level").replace("-Level", "")
                
                job = Job(
                    id=f"csv_{row['Job_ID']}",
                    role=row.get("Job_Title", "Software Engineer"),
                    company=row.get("Company", "Unknown"),
                    required_skills=row.get("Skills", "").lower(),
                    experience_level=exp_level,
                    education="Not Specified",
                    trend_score=float(trend_score)
                )
                db.add(job)
    else:
        # If empty and no CSV, populate with MOCK_JOB_DATA
        for job_data in MOCK_JOB_DATA:
            job = Job(
                id=job_data["id"],
                role=job_data["role"],
                company=job_data["company"],
                required_skills=",".join(job_data["required_skills"]),
                experience_level=job_data.get("experience_level", "Entry Level"),
                education=job_data.get("education", "Bachelor's"),
                trend_score=job_data["trend_score"]
            )
            db.add(job)
    
    db.commit()
