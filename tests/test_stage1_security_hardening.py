import pytest
import io
import sys
from unittest.mock import patch
from backend.app.config import settings
from backend.app.models import User
from backend.app.routers.parents import sms_provider
from backend.app.cli import provision_admin, validate_email, validate_password
from backend.app.auth import verify_password


def test_enable_demo_seeding_defaults_to_false():
    """Verify that demo seeding defaults to disabled for production safety."""
    assert hasattr(settings, "ENABLE_DEMO_SEEDING")
    assert settings.ENABLE_DEMO_SEEDING is False


def test_seed_database_respects_opt_in_guard(capsys):
    """Verify that seed_database does not run if ENABLE_DEMO_SEEDING is False and force=False."""
    from backend.app.seed import seed_database
    
    # Call without force
    seed_database(force=False)
    captured = capsys.readouterr()
    assert "Demo seeding is disabled by default" in captured.out


def test_parent_otp_does_not_disclose_otp_in_response(client, db_session, student_user_and_token):
    """Verify that OTP values are never disclosed in the API response payload."""
    from backend.app.models import Parent, ParentOTP
    student_user, _ = student_user_and_token
    phone = "9876543210"

    # Reset any existing Parent / ParentOTP for test isolation
    db_session.query(ParentOTP).filter(ParentOTP.mobile_number == phone).delete()
    db_session.query(Parent).filter(Parent.student_id == student_user.id).delete()
    db_session.commit()

    resp = client.post("/api/parent/request-otp", json={
        "roll_number": student_user.id,
        "mobile_number": phone
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "otp_debug" not in data
    assert "otp" not in data
    # Ensure message is neutral and does not claim SMS delivered if not configured
    assert "Please check your registered mobile device" in data["message"]


def test_sms_provider_does_not_log_plain_otp(capsys):
    """Verify that SMS provider console logs mask phone numbers and do not print the plain OTP."""
    from backend.app.routers.parents import DevelopmentSMSProvider, ProductionSMSProvider

    dev_provider = DevelopmentSMSProvider()
    prod_provider = ProductionSMSProvider()

    test_otp = "847291"
    dev_provider.send_otp("9876543210", test_otp)
    prod_provider.send_otp("9876543210", test_otp)

    captured = capsys.readouterr()
    # Ensure plain OTP was NOT output to stdout
    assert test_otp not in captured.out
    assert "No external SMS gateway configured" in captured.out


def test_admin_provisioning_cli_logic(db_session):
    """Test administrative provisioning validation, password hashing, and duplicate detection."""
    test_email = "test.newadmin@institution.edu"
    test_name = "New Test Admin"
    test_pass = "SecureAdminPass123"

    # Clean up any preexisting record for isolation
    db_session.query(User).filter(User.email == test_email).delete()
    db_session.commit()

    # 1. Validation error on invalid email
    with pytest.raises(ValueError, match="Invalid email address format"):
        provision_admin(db_session, "notanemail", test_name, test_pass)

    # 2. Validation error on short password
    with pytest.raises(ValueError, match="at least 8 characters"):
        provision_admin(db_session, test_email, test_name, "short")

    # 3. Successful provisioning
    admin_user = provision_admin(db_session, test_email, test_name, test_pass)
    assert admin_user.id is not None
    assert admin_user.email == test_email
    assert admin_user.role == "admin"
    assert admin_user.password_hash != test_pass
    assert verify_password(test_pass, admin_user.password_hash) is True

    # 4. Duplicate email rejection
    with pytest.raises(ValueError, match="already exists"):
        provision_admin(db_session, test_email, test_name, test_pass)

    # Clean up test user
    db_session.delete(admin_user)
    db_session.commit()


def test_admin_creation_not_exposed_via_unauthenticated_api(client):
    """Ensure there is no public endpoint permitting unauthorized admin creation."""
    # Attempting unauthenticated POST to common admin creation endpoints must fail with 401 or 404
    for endpoint in ["/api/admin/users", "/api/admin/create", "/api/auth/register-admin", "/api/admin/bootstrap"]:
        resp = client.post(endpoint, json={"email": "hacker@test.com", "password": "password123", "role": "admin"})
        assert resp.status_code in [401, 403, 404, 405]


def test_production_github_pages_cors_allowed(client):
    """Verify that requests from trusted GitHub Pages origin receive correct CORS headers."""
    resp = client.get("/api/health", headers={"Origin": "https://bhavya-labs.github.io"})
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "https://bhavya-labs.github.io"
    assert resp.headers.get("access-control-allow-credentials") == "true"


def test_untrusted_origin_cors_rejected(client):
    """Verify that untrusted origins do not receive CORS allow headers."""
    resp = client.get("/api/health", headers={"Origin": "https://malicious-site.example.com"})
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") is None


def test_cors_preflight_for_trusted_origins(client):
    """Verify preflight OPTIONS requests from GitHub Pages and localhost succeed."""
    for origin in ["https://bhavya-labs.github.io", "http://localhost:5173", "http://127.0.0.1:5173"]:
        resp = client.options("/api/auth/login", headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        })
        assert resp.status_code == 200
        assert resp.headers.get("access-control-allow-origin") == origin
        assert resp.headers.get("access-control-allow-credentials") == "true"

