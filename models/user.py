from sqlalchemy import Column, Integer, String, ForeignKey, Table, DateTime, Float, Text
from sqlalchemy.orm import relationship
from models.database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    
    saved_jobs = relationship("SavedJob", back_populates="user")
    analyses = relationship("ResumeAnalysis", back_populates="user")

class SavedJob(Base):
    __tablename__ = "saved_jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    job_id = Column(String, ForeignKey("jobs.id"))
    
    user = relationship("User", back_populates="saved_jobs")
    job = relationship("Job")

class ResumeAnalysis(Base):
    __tablename__ = "resume_analyses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    filename = Column(String)
    match_percentage = Column(Float)
    top_skills = Column(String)  # Comma-separated
    missing_skills = Column(String)  # Comma-separated
    full_data = Column(Text)  # JSON string for full results reconstruction
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="analyses")
