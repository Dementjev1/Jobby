import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./datababy_v4.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class JobEvaluationModel(Base):
    __tablename__ = "job_evaluations"

    # 🔑 Standard auto-incrementing integer index key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 📡 User Isolation & Tracking
    user_id = Column(String, nullable=False, index=True)
    search_keyword = Column(String, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Data Columns
    job_title = Column(String, nullable=True)
    company_name = Column(String, nullable=True)
    location = Column(String, default="Remote")
    match_score = Column(Integer, default=50)
    matching_skills = Column(Text, default="")  
    absent_skills = Column(Text, default="")    
    fit_analysis = Column(Text, default="")
    improvements = Column(Text, default="")
    scraped_url = Column(String, default="#")

def init_db():
    Base.metadata.create_all(bind=engine)