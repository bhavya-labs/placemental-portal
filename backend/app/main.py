
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.app.config import settings
from backend.app.database import engine, Base, SessionLocal
from backend.app.models import User
from backend.app.seed import seed_database
from backend.app.routers import (
    auth,
    students,
    companies,
    applications,
    analytics,
    ai,
    parents,
    permissions,
    attendance,
    activities,
    notifications,
    grievances,
    feedback,
    search,
    calendar,
)

import uvicorn


# ============================================================
# DATABASE MIGRATIONS
# ============================================================

def run_alembic_migrations():
    """
    Run Alembic migrations to bring the database schema
    up to the latest revision.
    """
    from pathlib import Path
    from alembic.config import Config
    from alembic import command

    # backend/app/main.py
    #         ↑
    # parents:
    # app -> backend -> project root
    base_dir = Path(__file__).resolve().parent.parent.parent

    ini_path = base_dir / "alembic.ini"

    # Fallback location
    if not ini_path.exists():
        ini_path = Path(__file__).resolve().parent.parent / "alembic.ini"

    if not ini_path.exists():
        print("Alembic configuration file not found. Skipping migrations.")
        return

    try:
        alembic_cfg = Config(str(ini_path))
        command.upgrade(alembic_cfg, "head")
        print("Alembic migrations completed successfully.")

    except Exception as e:
        # Do not prevent the application from starting if migrations
        # have already been applied or if the database has a recoverable
        # migration issue.
        print(f"Alembic migration info: {e}")


# Run migrations before application initialization.
run_alembic_migrations()


# ============================================================
# DATABASE TABLE INITIALIZATION
# ============================================================

try:
    Base.metadata.create_all(bind=engine)
    print("Database tables verified successfully.")
except Exception as e:
    print(f"Database table initialization warning: {e}")


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Centralized AI-powered college placement analytics "
        "& readiness prediction API."
    ),
    version="1.0.0",
)


# ============================================================
# CORS CONFIGURATION
# ============================================================

allowed_origins = [
    origin.strip()
    for origin in settings.FRONTEND_ORIGIN.split(",")
    if origin.strip() and origin.strip() != "*"
]

if not allowed_origins:
    allowed_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://bhavya-labs.github.io",
    ]

# Restrict production CORS to exact trusted origins (no wildcard regex allowed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ROUTERS
# ============================================================

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


# ============================================================
# STARTUP EVENT
# ============================================================

@app.on_event("startup")
def startup_event():
    """
    Perform lightweight database initialization during startup.

    IMPORTANT:
    ML model training is intentionally NOT performed here.

    Training the model during startup can take a long time and prevent
    Render from detecting the application's listening port. Model
    training should instead be performed separately through a dedicated
    command/job when required.
    """

    db = SessionLocal()

    try:
        user_count = db.query(User).count()

        if user_count == 0:
            if settings.ENABLE_DEMO_SEEDING:
                print(
                    "Database is empty and ENABLE_DEMO_SEEDING is enabled. "
                    "Seeding local development demo dataset..."
                )
                seed_database(force=True)
                print("Database demo seeding completed.")
            else:
                print(
                    "Database contains 0 accounts. "
                    "Automatic demo seeding is disabled (ENABLE_DEMO_SEEDING=False). "
                    "Use the administrative CLI to bootstrap initial user accounts."
                )
        else:
            print(
                f"Database already contains {user_count} accounts. "
                "Skipping database seeding."
            )

        # --------------------------------------------------------
        # Seed default faculty permissions if necessary
        # --------------------------------------------------------

        from backend.app.models import Permission, Faculty
        from datetime import datetime, timedelta

        permission_count = db.query(Permission).count()

        if permission_count == 0:
            faculties = db.query(Faculty).all()
            if faculties:
                print(
                    "Permissions table is empty. "
                    "Seeding default permissions for faculty coordinators..."
                )

            now = datetime.utcnow()
            start = now - timedelta(days=30)
            expiry = now + timedelta(days=365)

            for faculty in faculties:

                user = faculty.user
                dept_code = faculty.department.code

                # ------------------------------------------------
                # Permission 1: Student Performance
                # ------------------------------------------------

                p1 = Permission(
                    user_id=user.id,
                    module="Student Performance",
                    scope="DEPARTMENT",
                    scope_value=dept_code,
                    action="VIEW,CREATE,EDIT,DELETE,EXPORT",
                    start_date=start,
                    expiry_date=expiry,
                    status="Active",
                )

                # ------------------------------------------------
                # Permission 2: Placement Drives
                # ------------------------------------------------

                p2 = Permission(
                    user_id=user.id,
                    module="Placement Drives",
                    scope="DEPARTMENT",
                    scope_value=dept_code,
                    action="VIEW,CREATE,EDIT,DELETE,EXPORT",
                    start_date=start,
                    expiry_date=expiry,
                    status="Active",
                )

                # ------------------------------------------------
                # Permission 3: Analytics
                # ------------------------------------------------

                p3 = Permission(
                    user_id=user.id,
                    module="Analytics",
                    scope="DEPARTMENT",
                    scope_value=dept_code,
                    action="VIEW,CREATE,EDIT,DELETE,EXPORT",
                    start_date=start,
                    expiry_date=expiry,
                    status="Active",
                )

                db.add(p1)
                db.add(p2)
                db.add(p3)

            db.commit()

            print(
                "Default faculty coordinator permissions "
                "successfully seeded."
            )

        else:
            print(
                f"Permissions table already contains "
                f"{permission_count} records. Skipping permission seeding."
            )

        # --------------------------------------------------------
        # IMPORTANT:
        # Do NOT train the ML model here.
        # --------------------------------------------------------

        print(
            "Startup initialization completed. "
            "ML model training is skipped during application startup."
        )

    except Exception as e:
        print(f"Error during startup database setup: {e}")

    finally:
        db.close()


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/api/health")
def health_check():
    """
    Health endpoint used to verify that the API is running.
    """

    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "docs_url": "/docs",
    }


# ============================================================
# FRONTEND STATIC FILES
# ============================================================

# Project structure:
#
# placement portal/
# ├── backend/
# │   └── app/
# │       └── main.py
# │
# └── frontend/
#     └── dist/
#
# From backend/app/main.py:
# ../../../frontend/dist
#
# The existing code resolves the project root first.

frontend_dist = os.path.join(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(__file__)
        )
    ),
    "frontend",
    "dist",
)


if os.path.exists(frontend_dist):

    # --------------------------------------------------------
    # Frontend assets
    # --------------------------------------------------------

    assets_dir = os.path.join(frontend_dist, "assets")

    if os.path.exists(assets_dir):
        app.mount(
            "/assets",
            StaticFiles(directory=assets_dir),
            name="assets",
        )

    # --------------------------------------------------------
    # Root page
    # --------------------------------------------------------

    @app.get("/")
    def read_root():

        index_file = os.path.join(
            frontend_dist,
            "index.html",
        )

        if os.path.exists(index_file):
            return FileResponse(index_file)

        return {
            "status": "online",
            "project": settings.PROJECT_NAME,
            "docs_url": "/docs",
        }

    # --------------------------------------------------------
    # React SPA fallback
    # --------------------------------------------------------

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):

        # Do not intercept API or documentation routes.

        if (
            full_path.startswith("api/")
            or full_path in [
                "docs",
                "redoc",
                "openapi.json",
            ]
        ):
            raise HTTPException(
                status_code=404,
                detail="Endpoint not found",
            )

        file_path = os.path.join(
            frontend_dist,
            full_path,
        )

        if os.path.isfile(file_path):
            return FileResponse(file_path)

        index_file = os.path.join(
            frontend_dist,
            "index.html",
        )

        if os.path.exists(index_file):
            return FileResponse(index_file)

        raise HTTPException(
            status_code=404,
            detail="Page not found",
        )

else:

    # --------------------------------------------------------
    # Backend-only root
    # --------------------------------------------------------

    @app.get("/")
    def read_root():

        return {
            "status": "online",
            "project": settings.PROJECT_NAME,
            "docs_url": "/docs",
        }


# ============================================================
# LOCAL DEVELOPMENT
# ============================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))

    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
    )
