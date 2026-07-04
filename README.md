# Jobby.OS

**Jobby.OS** is an intelligent, end-to-end job scouting and evaluation system designed to automate the tedious aspects of job hunting. By leveraging modern web automation and AI-driven analysis, it allows users to discover relevant opportunities and evaluate their fit against job specifications in real-time.

## Project Overview
The system acts as a personal career assistant. It automates the extraction of job data from the web, runs the data through a custom AI analysis pipeline to calculate match scores, and presents the results through a clean, reactive web interface.

![Architecture Overview](image_82eba7.png)

## Key Features
* **Intelligent Scouting:** Uses `Playwright` to perform automated, reliable scraping of complex, dynamic job board websites.
* **AI-Powered Analysis:** Employs LLMs to compare resume data against job descriptions, providing detailed, actionable fit assessments.
* **Asynchronous Pipeline:** Built on `FastAPI` and `asyncio` to ensure high-performance, non-blocking execution of scraping and analysis tasks.
* **Data Persistence:** Utilizes `SQLAlchemy` and `SQLite` for structured, reliable storage of job leads and historical evaluation metrics.
* **Reactive Dashboard:** A custom web frontend that offers a seamless user experience, allowing for real-time visualization of job matches.

## Project Structure
```text
.
├── tools/              # Specialized utility scripts and modules
├── .gitignore          # Git exclusion rules
├── database.py         # SQLAlchemy models and DB configuration
├── index.html          # Frontend dashboard UI
├── pipeline.py         # Core asynchronous processing logic
├── requirements.txt    # Project dependencies
```
## Getting Started

### Prerequisites
* Python 3.x
* `pip` (Python package manager)

### Installation
1. Clone the repository:
   ```bash
   git clone -b not_loggeg_master <your-repo-url>
   cd Jobby.OS
    ```
2. Create an active venv environment
  ```bash
  python -m venv venv
  source venv/bin/activate  # On Windows: venv\Scripts\activate
  ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```
### Launch the server

```bash
  python server.py
```


Access the dashboard via your browser at the specified local port.

Built for efficiency, intelligence, and a better job-hunting experience.
  
