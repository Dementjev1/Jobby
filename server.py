import sys
import asyncio

# 🛠️ Fix Windows ProactorEventLoop compatibility issue with Playwright subprocesses
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


import re
import json
import time
import asyncio
from fastapi import FastAPI, Depends, UploadFile, Form, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from playwright.async_api import async_playwright
import io
from fastapi import UploadFile
from pypdf import PdfReader

from database import SessionLocal, JobEvaluationModel, init_db
from pipeline import JobPipeline

app = FastAPI()

# Ensure fresh DB initialization on boot
init_db()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def extract_text_from_pdf(file: UploadFile) -> str:
    """
    Reads an uploaded PDF file straight from the memory buffer 
    and converts all pages into a single plain text string.
    """
    # Read raw bytes from the FastAPI memory buffer
    file_bytes = await file.read()
    await file.seek(0)  # Reset stream pointer
    
    # Load bytes into an in-memory binary stream
    pdf_stream = io.BytesIO(file_bytes)
    reader = PdfReader(pdf_stream)
    
    # Extract text from each page and combine
    text_content = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text_content.append(page_text)
            
    return "\n".join(text_content).strip()

@app.get("/", response_class=HTMLResponse)
def read_root():
    with open("index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

# =====================================================================
# API: Fetch Isolated Records
# =====================================================================
@app.get("/api/evaluations")
def get_user_evaluations(client_id: str = Query(None), db: Session = Depends(get_db)):
    if not client_id:
        return []
    
    records = db.query(JobEvaluationModel)\
                .filter(JobEvaluationModel.user_id == client_id)\
                .order_by(JobEvaluationModel.created_at.desc())\
                .all()
    
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
        print(f"⚡ Starting operational sequence for User: {client_id} -> Query: '{keyword}'")
        
        # 1. Read incoming uploaded CV dossier bytes
        resume_text = await extract_text_from_pdf(file)
        job = JobPipeline(client_iddd=client_id, cv_text=resume_text, search_keyword=keyword)

        await job.run_pipeline()
        
    except Exception as e:
        print(f"❌ Server Engine Exception: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)