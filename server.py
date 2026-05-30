import os
import time
from fastapi import FastAPI, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv

# Inject all configurations from your .env file
load_dotenv()

app = FastAPI(title="Jobby.OS - Sandbox Module")

# 1. SERVE THE HTML FRONTEND INTERFACE
@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    if not os.path.exists("index.html"):
        raise HTTPException(status_code=404, detail="index.html file not found in directory.")
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

# 2. SANDBOX MOCK SCOUT ENDPOINT 
@app.post("/api/scout")
async def mock_recruitment_scanner(keyword: str = Form(...), file: UploadFile = Form(...)):
    try:
        # Read the uploaded PDF out of memory streams
        pdf_bytes = await file.read()
        
        # 🧪 TEST: Verify the file is loading correctly!
        print("--------------------------------------------------")
        print(f"📡 API GATEWAY RECEIVED REQUEST!")
        print(f"🔑 Search Keyword: {keyword}")
        print(f"📄 Uploaded File Name: {file.filename}")
        print(f"⚖️ File Size in Memory: {len(pdf_bytes)} bytes")
        print("--------------------------------------------------")

        # Simulate a 2-second processing delay so you can see the spinning animation
        time.sleep(2)

        # Send back a mock JSON payload that matches what our React page expects to render
        mock_jobs = [
            {
                "id": 1,
                "title": f"Senior {keyword} Specialist",
                "company": "Bolt (Mock Data)",
                "location": "Tallinn, Estonia",
                "match": 95,
                "analysis": "🟢 Perfect match!\nYour uploaded document aligns beautifully with this mock role infrastructure."
            },
            {
                "id": 2,
                "title": f"Junior {keyword} Engineer",
                "company": "Wise (Mock Data)",
                "location": "Remote",
                "match": 81,
                "analysis": "🟡 Average Match.\nMissing explicit Python framework documentation within the uploaded resume core structural footprint."
            }
        ]

        return {"status": "success", "jobs": mock_jobs}

    except Exception as server_err:
        print(f"🚨 Sandbox Error: {server_err}")
        return {"status": "error", "message": str(server_err)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)