import os
import io
import asyncio
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from pypdf import PdfReader
from dotenv import load_dotenv

# Import your database components
from database import SessionLocal, JobEvaluationModel, init_db

load_dotenv()
init_db()

app = FastAPI(title="Jobby.OS - Production Core Engine")

# 🔒 Touchpoint: Ensure full CORS parameters are open so the browser accepts data transmissions
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 🏡 Serve Frontend Interface
@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    if not os.path.exists("index.html"):
        raise HTTPException(status_code=404, detail="index.html file not found in directory.")
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

# 📋 Fetch historical records endpoint
@app.get("/api/evaluations", response_model=List[dict])
def list_stored_evaluations(db: Session = Depends(get_db)):
    try:
        records = db.query(JobEvaluationModel).order_by(JobEvaluationModel.id.desc()).all()
        return [{
            "id": r.id,
            "job_title": r.job_title,
            "company_name": r.company_name,
            "scraped_url": r.scraped_url,
            "match_score": r.evaluation_data.get("match_score", 0) if isinstance(r.evaluation_data, dict) else 0,
            "created_at": r.created_at.isoformat()
        } for r in records]
    except Exception as e:
        print(f"Database list error: {e}")
        return []

# 📡 Active Pipeline Scout Endpoint
@app.post("/api/scout")
async def run_live_recruitment_scanner(
    keyword: str = Form(...), 
    file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    try:
        pdf_bytes = await file.read()
        print("--------------------------------------------------")
        print(f"📡 CORE PIPELINE ENGAGED!")
        print(f"🔑 Keyword: {keyword} | File: {file.filename}")
        
        pdf_stream = io.BytesIO(pdf_bytes)
        reader = PdfReader(pdf_stream)
        cv_text = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                cv_text += text + "\n"
        
        cv_text = cv_text.strip()
        print(f"✅ Extracted: {len(cv_text)} characters.")
        print("--------------------------------------------------")

        # Mock delay to confirm execution lifecycle
        await asyncio.sleep(1)

        # Grab latest row entries from SQLite
        results = db.query(JobEvaluationModel).order_by(JobEvaluationModel.id.desc()).all()
        
        formatted_jobs = []
        for r in results:
            formatted_jobs.append({
                "id": r.id,
                "title": r.job_title,
                "company": r.company_name,
                "match": r.evaluation_data.get("match_score", 0) if isinstance(r.evaluation_data, dict) else 0,
                "analysis": r.evaluation_data.get("fit_analysis", "No raw analysis summary compiled.") if isinstance(r.evaluation_data, dict) else "No data."
            })

        return {"status": "success", "jobs": formatted_jobs}

    except Exception as server_err:
        print(f"🚨 Pipeline Endpoint Failure: {server_err}")
        return {"status": "error", "message": str(server_err)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)