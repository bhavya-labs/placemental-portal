import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.app.config import settings
from backend.app.database import engine, Base, SessionLocal
from backend.app.models import User
from backend.app.seed import seed_database
from backend.app.routers import auth, students, companies, applications, analytics, ai, parents, permissions, attendance, activities, notifications, grievances, feedback, search, calendar
import uvicorn

# Run Alembic schema migrations to head revision
def run_alembic_migrations():
    """Execute Alembic migrations to ensure database schema and indexes are up to date."""
    from pathlib import Path
    from alembic.config import Config
    from alembic import command

    base_dir = Path(__file__).resolve().parent.parent.parent
    ini_path = base_dir / "alembic.ini"
    if not ini_path.exists():
        ini_path = Path(__file__).resolve().parent.parent / "alembic.ini"

    if ini_path.exists():
        try:
            alembic_cfg = Config(str(ini_path))
            command.upgrade(alembic_cfg, "head")
        except Exception as e:
            print(f"Alembic auto-migration info: {e}")

run_alembic_migrations()


# Initialize database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Centralized AI-powered college placement analytics & readiness prediction API.",
    version="1.0.0"
)

# CORS configuration with explicit origin allowlist
allowed_origins = [origin.strip() for origin in settings.FRONTEND_ORIGIN.split(",") if origin.strip()]
if not allowed_origins:
    allowed_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]

if "*" in allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=".*",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include Routers
app.include_router(auth.router)
app.include_router(students.router)
app.include_router(students.student_alias_router)
app.include_router(companies.router)
app.include_router(applications.router)
app.include_router(analytics.router)
app.include_router(ai.router)
app.include_router(parents.router)
app.include_router(permissions.router)
app.include_router(attendance.router)
app.include_router(activities.router)
app.include_router(notifications.router)
app.include_router(grievances.router)
app.include_router(feedback.router)
app.include_router(search.router)
app.include_router(calendar.router)

@app.on_event("startup")
def startup_event():
    # Automatically seed the database on startup if it contains no users
    db = SessionLocal()
    try:
        user_count = db.query(User).count()
        if user_count == 0:
            print("Database is empty. Initiating automatic seeding of 3,000 students, 150+ companies, and models training...")
            seed_database()
        else:
            print(f"Database already contains {user_count} accounts. Skipping seeding. Training ML model on startup...")
            from backend.app.ml.predictor import predictor
            predictor.train_model(db)

        # Seed default permissions for faculty if permissions table is empty
        from backend.app.models import Permission, Faculty
        from datetime import datetime, timedelta
        permission_count = db.query(Permission).count()
        if permission_count == 0:
            print("Permissions table is empty. Seeding default permissions for faculty coordinators...")
            faculties = db.query(Faculty).all()
            now = datetime.utcnow()
            start = now - timedelta(days=30)
            expiry = now + timedelta(days=365)
            for f in faculties:
                user = f.user
                dept_code = f.department.code
                # Perm 1: Student Performance
                p1 = Permission(
                    user_id=user.id,
                    module="Student Performance",
                    scope="DEPARTMENT",
                    scope_value=dept_code,
                    action="VIEW,CREATE,EDIT,DELETE,EXPORT",
                    start_date=start,
                    expiry_date=expiry,
                    status="Active"
                )
                # Perm 2: Placement Drives
                p2 = Permission(
                    user_id=user.id,
                    module="Placement Drives",
                    scope="DEPARTMENT",
                    scope_value=dept_code,
                    action="VIEW,CREATE,EDIT,DELETE,EXPORT",
                    start_date=start,
                    expiry_date=expiry,
                    status="Active"
                )
                # Perm 3: Analytics
                p3 = Permission(
                    user_id=user.id,
                    module="Analytics",
                    scope="DEPARTMENT",
                    scope_value=dept_code,
                    action="VIEW,CREATE,EDIT,DELETE,EXPORT",
                    start_date=start,
                    expiry_date=expiry,
                    status="Active"
                )
                db.add(p1)
                db.add(p2)
                db.add(p3)
            db.commit()
            print("Default faculty coordinator permissions successfully seeded!")
    except Exception as e:
        print(f"Error checking database setup: {e}")
    finally:
        db.close()

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "docs_url": "/docs"
    }

# Check for compiled frontend bundle for unified deployment (e.g. Render)
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist")

if os.path.exists(frontend_dist):
    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/")
    def read_root():
        index_file = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {
            "status": "online",
            "project": settings.PROJECT_NAME,
            "docs_url": "/docs"
        }

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Do not intercept API, docs, or OpenAPI schema
        if full_path.startswith("api/") or full_path in ["docs", "redoc", "openapi.json"]:
            raise HTTPException(status_code=404, detail="Endpoint not found")
        
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        
        index_file = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        raise HTTPException(status_code=404, detail="Page not found")
else:
    @app.get("/")
    def read_root():
        return {
            "status": "online",
            "project": settings.PROJECT_NAME,
            "docs_url": "/docs"
        }

if __name__ == "__main__":
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
