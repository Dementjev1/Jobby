import sys
import io
import uvicorn
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, Depends, UploadFile, Form, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from pypdf import PdfReader

# Your project imports
from database import SessionLocal, JobEvaluationModel, init_db
from pipeline import JobPipeline

# 1. Define the lifespan context manager (The "modern" way to manage startup/shutdown)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize the executor
    app.state.executor = ThreadPoolExecutor(max_workers=3)
    init_db()  # Initialize DB here
    yield
    # Shutdown: Cleanly stop the executor
    app.state.executor.shutdown(wait=True)

app = FastAPI(lifespan=lifespan)

# Helper function
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def extract_text_from_pdf(file: UploadFile) -> str:
    file_bytes = await file.read()
    await file.seek(0)
    pdf_stream = io.BytesIO(file_bytes)
    reader = PdfReader(pdf_stream)
    text_content = [page.extract_text() for page in reader.pages if page.extract_text()]
    return "\n".join(text_content).strip()

@app.get("/", response_class=HTMLResponse)
def read_root():
    with open("index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/api/evaluations")
def get_user_evaluations(client_id: str = Query(None), db: Session = Depends(get_db)):
    if not client_id:
        return []
    records = db.query(JobEvaluationModel).filter(JobEvaluationModel.user_id == client_id).order_by(JobEvaluationModel.created_at.desc()).all()


    output = []
    for r in records:
        output.append({
            "id": r.id, # Returns standard sequential ID (e.g. 1, 2, 3)
            "job_title": r.job_title or "Position Profile",
            "company_name": r.company_name or "Tech Enterprise",
            "location": r.location or "Remote",
            "match_score": r.match_score or 0,
            "matching_skills": [s.strip() for s in r.matching_skills.split(",")] if r.matching_skills else [],
            "absent_skills": [s.strip() for s in r.absent_skills.split(",")] if r.absent_skills else [],
            "fit_analysis": r.fit_analysis or "",
            "improvements": [line.strip() for line in r.improvements.split("\n") if line.strip()] if r.improvements else [],
            "scraped_url": r.scraped_url or "#"
        })
    return output

# =====================================================================
# API: Run Scraper Pipeline & Process Loop
# =====================================================================
@app.post("/api/scout")
async def process_scout_pipeline(
    file: UploadFile,
    keyword: str = Form(...),
    client_id: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        print(f"⚡ Starting operational sequence for User: {client_id}")
        resume_text = await extract_text_from_pdf(file)
        
        # Instantiate pipeline
        job = JobPipeline(client_iddd=client_id, cv_text=resume_text, search_keyword=keyword)

        # ACCESS EXECUTOR FROM app.state
        await job.run_pipeline(app.state.executor)

        return {'status': 'completed', 'message': 'Job processing completed successfully.'}
        
    except Exception as e:
        print(f"❌ Server Engine Exception: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)