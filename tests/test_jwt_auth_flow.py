import pytest
from datetime import timedelta
from backend.app.models import User
from backend.app.auth import create_access_token

def test_valid_login(client, db_session):
    from backend.app.routers.auth import login_rate_limiter
    login_rate_limiter._attempts.clear()

    admin = db_session.query(User).filter(User.role == "admin").first()
    assert admin is not None, "Admin user required for login test"

    resp = client.post("/api/auth/login", json={
        "email": admin.email,
        "password": "password123"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["role"] == "admin"
    assert data["token_type"] == "bearer"

def test_invalid_password_returns_401(client):
    resp = client.post("/api/auth/login", json={
        "email": "admin@college.edu",
        "password": "definitely_wrong_password_xyz"
    })
    assert resp.status_code in [401, 429]
    if resp.status_code == 401:
        assert "Incorrect email or password" in resp.json()["detail"]

def test_expired_token_rejected(client):
    # Generate an already expired token (negative delta)
    expired_token = create_access_token(
        data={"sub": "admin@college.edu", "role": "admin"},
        expires_delta=timedelta(minutes=-10)
    )
    headers = {"Authorization": f"Bearer {expired_token}"}
    resp = client.get("/api/auth/profile", headers=headers)
    assert resp.status_code == 401
    assert "Token has expired" in resp.json()["detail"]

def test_role_enforcement_student_forbidden_from_admin_routes(client, student_user_and_token):
    student_user, student_token = student_user_and_token
    headers = {"Authorization": f"Bearer {student_token}"}

    # Student tries to create a company -> should be 403 Forbidden
    resp = client.post("/api/companies", json={
        "name": "Unauthorized Company Attempt",
        "industry": "IT"
    }, headers=headers)
    assert resp.status_code == 403
    assert "Forbidden" in resp.json()["detail"] or "Access denied" in resp.json()["detail"]

    # Student accessing their own profile -> 200 OK
    resp_profile = client.get("/api/auth/profile", headers=headers)
    assert resp_profile.status_code == 200
    assert resp_profile.json()["role"] == "student"
