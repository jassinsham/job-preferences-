from sqlalchemy import Column, Integer, String, Float
from models.database import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, index=True)
    role = Column(String, index=True)
    company = Column(String, index=True)
    location = Column(String, default="Remote")
    phone_number = Column(String, nullable=True)
    employment_type = Column(String, default="Full-Time")
    experience_level = Column(String, default="Entry Level")
    education = Column(String, default="Bachelor's")
    industry = Column(String, nullable=True)
    remote_type = Column(String, default="Remote")
    required_skills = Column(String)  # Comma-separated string
    salary_lpa = Column(String, nullable=True)
    company_rating = Column(Float, nullable=True)
    applicants_count = Column(Integer, default=0)
    posted_days_ago = Column(Integer, default=1)
    trend_score = Column(Float)
