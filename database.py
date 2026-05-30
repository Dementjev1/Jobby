import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. Target your local file on the Pi 5 and apply the 30-second concurrency fix
DATABASE_URL = "sqlite:///datababy.db"
engine = create_engine(DATABASE_URL, connect_args={"timeout": 30, "check_same_thread": False})

# 2. Create the session maker tool
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 3. Define the database table map
class JobEvaluationModel(Base):
    __tablename__ = 'job_evaluations'

    id = Column(Integer, primary_key=True, index=True)
    job_title = Column(String, nullable=False)
    company_name = Column(String, nullable=False)
    
    # 🧠 SQLAlchemy automatically translates Python dictionaries into SQLite text strings
    evaluation_data = Column(JSON, nullable=False) 
    
    created_at = Column(DateTime, default=datetime.datetime.now().date())

# 4. Helper function to spin up the database file automatically if it's missing
def init_db():
    Base.metadata.create_all(bind=engine)