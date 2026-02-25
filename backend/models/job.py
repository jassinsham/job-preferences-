from sqlalchemy import Column, Integer, String, Float
from models.database import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, index=True)
    role = Column(String, index=True)
    company = Column(String, index=True)
    required_skills = Column(String) # Comma-separated or JSON string, let's use comma-separated for simplicity in SQLite 
    experience_level = Column(String, default="Entry Level")
    education = Column(String, default="Bachelor's")
    trend_score = Column(Float)
