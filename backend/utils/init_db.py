import csv
import os
import glob
from sqlalchemy.orm import Session
from models.job import Job
from services.skill_matcher import MOCK_JOB_DATA

def init_db_data(db: Session):
    # Check if we already have jobs
    if db.query(Job).first():
        return
        
    # Find all CSV files in the project root (one level up from backend)
    # The script runs from the backend directory
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    csv_files = glob.glob(os.path.join(project_root, "*.csv"))
    
    if csv_files:
        for csv_path in csv_files:
            print(f"Ingesting data from {os.path.basename(csv_path)}...")
            try:
                with open(csv_path, mode='r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # Some files might have a BOM in the first column header
                        job_id_key = next((key for key in row.keys() if 'Job_ID' in key), 'Job_ID')
                        
                        # Derive a trend score inversely related to Post_Days_Ago
                        try:
                            days_ago = int(row.get('Post_Days_Ago', 0) or 0)
                        except ValueError:
                            days_ago = 0
                            
                        trend_score = max(70, 100 - days_ago)
                        
                        # Sanitize experience level strings
                        exp_level = row.get("Experience_Required", "Entry Level")
                        
                        # Create unique ID to avoid collisions across files
                        base_id = row.get(job_id_key, "unknown")
                        unique_id = f"{os.path.basename(csv_path)}_{base_id}"
                        
                        # Check if job already exists (avoid duplicates if same file processed twice or overlapping data)
                        if db.query(Job).filter(Job.id == unique_id).first():
                            continue

                        job = Job(
                            id=unique_id,
                            role=row.get("Job_Role", "Software Engineer"),
                            company=row.get("Company", "Unknown"),
                            location=row.get("Location", "Remote"),
                            phone_number=row.get("Phone_Number", "Not Available"),
                            employment_type=row.get("Employment_Type", "Full-Time"),
                            experience_level=exp_level,
                            education=row.get("Education_Level", "Not Specified"),
                            industry=row.get("Industry"),
                            remote_type=row.get("Remote_Type", "Remote"),
                            required_skills=row.get("Skills_Required", "").lower(),
                            salary_lpa=row.get("Salary_LPA", "Not Specified"),
                            company_rating=float(row.get("Company_Rating", 0.0) or 0.0),
                            applicants_count=int(row.get("Applicants_Count", 0) or 0),
                            posted_days_ago=days_ago,
                            trend_score=float(trend_score)
                        )
                        db.add(job)
                db.commit() # Commit after each file
            except Exception as e:
                print(f"Error processing {csv_path}: {e}")
                db.rollback()
    else:
        # If no CSVs found, populate with MOCK_JOB_DATA
        for job_data in MOCK_JOB_DATA:
            job = Job(
                id=job_data["id"],
                role=job_data["role"],
                company=job_data["company"],
                required_skills=",".join(job_data["required_skills"]),
                experience_level=job_data.get("experience_level", "Entry Level"),
                education=job_data.get("education", "Bachelor's"),
                location="Remote",
                employment_type="Full-Time",
                posted_days_ago=1,
                trend_score=job_data["trend_score"]
            )
            db.add(job)
        db.commit()
