# Deployment Guide: Render.com Cloud Deployment

This comprehensive guide walks you through deploying the **AI-Powered Placement Intelligence and Student Career Analytics Platform** to [Render](https://render.com) using the Free tier.

---

## 🏗 Architecture Overview

The application is configured as a **Unified Full-Stack Web Service**:
- **Backend (FastAPI)**: Serves all REST APIs, machine learning pipelines, NLP analyzers, and automated schema migrations.
- **Frontend (React + Vite + TypeScript)**: Built during deployment into static assets (`frontend/dist`), automatically mounted and served by FastAPI with client-side SPA routing support.
- **Single Domain / Zero CORS Issues**: Both frontend and backend run on the exact same origin (`https://<service-name>.onrender.com`), eliminating cross-origin resource sharing errors and browser cookie/header issues.
- **Free Tier Compatible**: Fits 100% within Render's single free web service allowance (750 free hours/month).

---

## 🚀 Method 1: Automated Blueprint Deployment (Recommended)

Render Blueprints read the included `render.yaml` configuration file and automatically configure all build steps, run commands, and environment variables.

### Step 1: Push Code to GitHub

If you haven't already pushed your code to a GitHub repository, run the following commands from the project root:

```bash
# 1. Stage all files
git add .

# 2. Commit the deployment files
git commit -m "Configure unified full-stack Render deployment"

# 3. Rename branch to main
git branch -M main

# 4. Link your GitHub repository (replace with your repo URL)
git remote add origin https://github.com/<YOUR-USERNAME>/<YOUR-REPO-NAME>.git

# 5. Push to GitHub
git push -u origin main
```

### Step 2: Deploy Blueprint on Render

1. Sign up or log in to [dashboard.render.com](https://dashboard.render.com/).
2. In the top navigation bar, click **New +** and select **Blueprint**.
3. Connect your GitHub account (if not already connected) and select your repository.
4. Render will detect `render.yaml`. Click **Apply**.
5. Render will immediately initiate the build process:
   - Installing Python dependencies (`pip install -r backend/requirements.txt`)
   - Installing Node packages and compiling frontend bundle (`npm install && npm run build`)
   - Applying database migrations (`python -m alembic upgrade head`)
   - Starting the service (`uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`)

---

## 🛠 Method 2: Manual Dashboard Setup

If you prefer to configure the service manually through the Render web UI:

1. Go to [dashboard.render.com](https://dashboard.render.com/).
2. Click **New +** > **Web Service**.
3. Select **Build and deploy from a Git repository** and connect your repository.
4. Fill in the service configuration details:

| Configuration Field | Value |
| :--- | :--- |
| **Name** | `placement-portal` *(or your choice)* |
| **Region** | `Oregon (US West)` *(or closest region)* |
| **Branch** | `main` |
| **Runtime** | `Python 3` |
| **Build Command** | `./build.sh` |
| **Start Command** | `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT` |
| **Instance Type** | `Free` |

5. Scroll down to **Environment Variables** and add the following:

| Key | Value | Purpose |
| :--- | :--- | :--- |
| `PYTHON_VERSION` | `3.11.8` | Ensures Python 3.11 runtime |
| `NODE_VERSION` | `20.11.0` | Enables Node.js in the build environment |
| `SECRET_KEY` | *(Click "Generate" or enter 64-char string)* | JWT authentication encryption key |
| `DATABASE_URL` | `sqlite:///./placement_portal.db` | Application SQLite database path |
| `FRONTEND_ORIGIN` | `*` | Allowed CORS origins |
| `SMS_ENV` | `dev` | Dev mode for simulated SMS OTP |
| `PROJECT_NAME` | `AI-Powered Placement Intelligence Platform` | Platform metadata title |

6. Under **Advanced Settings**:
   - **Health Check Path**: `/api/health`
   - **Auto-Deploy**: `Yes` (automatically redeploys whenever you push to `main`)

7. Click **Create Web Service**.

---

## 🔍 Verification & Health Checks

Once the build finishes and status displays **Live**:

1. **Frontend Application**:
   Navigate to `https://<your-service-name>.onrender.com/` to verify the interactive landing page and role-based login tabs.
2. **Health Check**:
   Navigate to `https://<your-service-name>.onrender.com/api/health` — should return:
   ```json
   {
     "status": "healthy",
     "project": "AI-Powered Placement Intelligence Platform",
     "docs_url": "/docs"
   }
   ```
3. **Interactive Swagger Documentation**:
   Navigate to `https://<your-service-name>.onrender.com/docs` to test all 40+ endpoints live.

---

## 🔑 Pre-Seeded Demonstration Credentials

When first deployed, the platform automatically initializes and seeds the database with realistic academic and placement records:

| Role | Email / Username | Default Password | Access Scope |
| :--- | :--- | :--- | :--- |
| **Platform Administrator** | `admin@platform.edu` | `password123` | Full administrative control, system logs, AI metrics |
| **Faculty Coordinator (CSE)** | `rajesh.cse@platform.edu` | `password123` | CSE Department, at-risk tracking, drive management |
| **Faculty Coordinator (ECE)** | `murthy.ece@platform.edu` | `password123` | ECE Department records and performance metrics |
| **Sample Student** | `student1@platform.edu` | `password123` | Student dashboard, readiness score, drive applications |
| **Parent Portal** | Direct Phone / Roll No. | Dev OTP: `123456` | Student attendance, academic progress, placement alerts |

---

## 💡 Important Notes on Free-Tier Hosting

1. **Cold Starts (Spin Down)**:
   On Render's Free tier, services spin down after 15 minutes of inactivity. When a new request arrives, it may take 30–50 seconds for the container to wake up. This is standard free-tier behavior.
2. **Persistent Storage**:
   Render's free tier uses an ephemeral disk (reset on container rebuilds). The startup script automatically re-creates tables, runs migrations, and seeds the sample dataset whenever a fresh instance is launched. If persistent long-term storage across re-deploys is required in production, link a Render PostgreSQL database by updating `DATABASE_URL`.
