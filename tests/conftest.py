import sys
import os
from pathlib import Path
from datetime import date, timedelta

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.models import User, Student, Department, Company, PlacementDrive, Application
from backend.app.auth import create_access_token, get_password_hash

@pytest.fixture(scope="session")
def client():
    return TestClient(app)

@pytest.fixture(scope="function")
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(scope="function")
def admin_token(db_session):
    admin = db_session.query(User).filter(User.role == "admin").first()
    email = admin.email if admin else "admin@college.edu"
    return create_access_token(data={"sub": email, "role": "admin"})

@pytest.fixture(scope="function")
def faculty_token(db_session):
    faculty = db_session.query(User).filter(User.role == "faculty").first()
    email = faculty.email if faculty else "faculty.cse@college.edu"
    return create_access_token(data={"sub": email, "role": "faculty"})

@pytest.fixture(scope="function")
def student_user_and_token(db_session):
    student_user = db_session.query(User).join(Student).first()
    if not student_user:
        raise RuntimeError("No student profile found in database!")
    token = create_access_token(data={"sub": student_user.email, "role": "student"})
    return student_user, token
