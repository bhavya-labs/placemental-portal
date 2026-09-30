# AP-CPIP — Fresh Clone Setup & Deployment Guide

**Project**: AI-Powered Placement Intelligence & Student Career Analytics Platform (AP-CPIP)  
**Architecture**: FastAPI + SQLAlchemy (SQLite) Backend & React 19 + TypeScript + Vite Frontend  
**Tested Environment**: Windows 10/11 & Ubuntu Linux with Python 3.11 and Node.js 20  

---

## 1. Prerequisites

Before installing the platform, ensure you have the following installed on your machine:
* **Python**: `3.10` or higher (verified with Python `3.11.8`)
* **Node.js**: `18.0` or higher & **npm** `9.0` or higher
* **Git**: `2.30` or higher

---

## 2. Step-by-Step Installation

### Step 2.1: Clone the Repository & Enter Directory
```bash
git clone <repository_url> "placement portal"
cd "placement portal"
```

---

### Step 2.2: Backend Environment Configuration

#### 1. Create and Activate a Python Virtual Environment
**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**On Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

#### 2. Install Backend Dependencies
```bash
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
```

#### 3. Configure the Environment Variables
Copy the provided `.env.example` to `.env`:
* **Windows (PowerShell):**
  ```powershell
  Copy-Item .env.example .env
  ```
* **Linux / macOS:**
  ```bash
  cp .env.example .env
  ```

*(The `.env` file comes pre-configured with safe local defaults: SQLite database URL, dev secret keys, and CORS origins).*

---

### Step 2.3: Database Setup & Migrations

#### 1. Apply Alembic Migrations
Run Alembic to apply all schema migrations and database indexes up to the latest revision:
```bash
python -m alembic upgrade head
```

#### 2. Seed Initial Demonstration Data (Fresh Clones Only)
If you cloned the repository without an existing `placement_portal.db` file, populate the database with the pre-configured academic dataset (3,000 students, 155 companies, 25 drives):
```bash
python -m backend.app.seed
```

---

### Step 2.4: Launch the Backend Server

Start the FastAPI backend with hot-reload enabled:
```bash
python backend/run.py
```
* **API Documentation (Swagger UI)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **ReDoc Interactive Reference**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
* **Health Check**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

### Step 2.5: Frontend Setup & Execution

Open a separate terminal window and navigate to the `frontend/` directory:

```bash
cd "placement portal/frontend"
npm install
npm run dev
```

The React + Vite frontend will start immediately:
* **Frontend Application URL**: [http://localhost:5173](http://localhost:5173)

---

## 3. Running Automated Tests & CI Audit

To verify system correctness and demonstrate test coverage during evaluations or vivas:

### Run the Full Pytest Test Suite
```bash
# From the project root with virtual environment active:
python -m pytest
```
*Runs all 27 automated unit and integration test cases covering Security Hardening (Phase 1), Database Indexes & Pagination (Phase 2), ML Rigor & Metrics (Phase 3), Eligibility Rules, Readiness Formulas, JWT Auth, and Parent OTP Rate Limiting (Phase 5).*

### Run the End-to-End Local CI Pipeline
```bash
python run_ci.py
```
*Executes the complete CI pipeline locally: Alembic migration check, Phase 1 security audit, Phase 2 database audit, Phase 3 ML metrics audit, and the Pytest 27-test automated suite.*

---

## 4. Demonstration Accounts & Login Credentials

All demonstration accounts use the standard seed credentials:

| Role | Email / Identifier | Password | Access Scope |
| :--- | :--- | :--- | :--- |
| **System Administrator** | `admin@platform.edu` | `password123` | Institutional Master Dashboard, RBAC Console, Audit Logs |
| **Faculty Coordinator (CSE)** | `faculty.cse@platform.edu` | `password123` | CSE Department Cockpit, Drive Scheduler, Student 360 |
| **Faculty Coordinator (ECE)** | `faculty.ece@platform.edu` | `password123` | ECE Department Cockpit, Drive Scheduler, Student 360 |
| **Student Account** | `student1@platform.edu` | `password123` | Student Dashboard, Applications, AI Readiness, ATS Scanner |
| **Parent Portal** | Roll Number: `1`<br>Mobile: `9876500001` | Dynamic OTP | Parent Transparency Portal (OTP logged to console/debug) |

---

## 5. Troubleshooting & FAQ

### Issue: "Address already in use" on port 8000 or 5173
* **Backend**: Check if another uvicorn process is running (`netstat -ano | findstr :8000`). Terminate the process and restart `python backend/run.py`.
* **Frontend**: Vite will automatically offer port `5174` if `5173` is occupied. If running on `5174`, add `http://localhost:5174` to `FRONTEND_ORIGIN` in `.env`.

### Issue: "No module named backend"
* Ensure commands are executed from the **project root directory** (`placement portal/`), not from inside `backend/` or `backend/app/`.

### Issue: "Alembic Target database is not up to date"
* Run `python -m alembic upgrade head` to apply all pending schema migrations.
