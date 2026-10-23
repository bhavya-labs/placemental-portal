import pytest
from datetime import datetime, timedelta
from backend.app.models import Student, Parent, ParentOTP
from backend.app.routers.parents import sms_provider

def test_otp_request_and_cooldown(client, db_session, student_user_and_token):
    student_user, _ = student_user_and_token
    student_id = student_user.id
    phone = "9876500001"

    # Reset any existing Parent / ParentOTP for isolation
    db_session.query(ParentOTP).filter(ParentOTP.mobile_number == phone).delete()
    db_session.query(Parent).filter(Parent.student_id == student_id).delete()
    db_session.commit()

    # 1. First OTP request succeeds
    resp1 = client.post("/api/parent/request-otp", json={
        "roll_number": student_id,
        "mobile_number": phone
    })
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["success"] is True
    # SECURE: OTP must NEVER be disclosed in response payload
    assert "otp_debug" not in data1
    assert phone in getattr(sms_provider, "last_dispatched_otp", {})

    # 2. Immediate second request triggers cooldown rate limit
    resp2 = client.post("/api/parent/request-otp", json={
        "roll_number": student_id,
        "mobile_number": phone
    })
    assert resp2.status_code == 400
    assert "Please wait" in resp2.json()["detail"]

def test_otp_failed_attempts_lockout(client, db_session, student_user_and_token):
    student_user, _ = student_user_and_token
    student_id = student_user.id
    phone = "9876500002"

    # Setup parent and fresh OTP record in DB directly to bypass cooldown
    db_session.query(ParentOTP).filter(ParentOTP.mobile_number == phone).delete()
    parent = db_session.query(Parent).filter(Parent.student_id == student_id).first()
    if not parent:
        parent = Parent(student_id=student_id, parent_name="Guardian", mobile_number=phone)
        db_session.add(parent)
    else:
        parent.mobile_number = phone
    db_session.commit()

    # Request fresh OTP
    resp_init = client.post("/api/parent/request-otp", json={
        "roll_number": student_id,
        "mobile_number": phone
    })
    assert resp_init.status_code == 200
    assert "otp_debug" not in resp_init.json()
    valid_otp = getattr(sms_provider, "last_dispatched_otp", {}).get(phone)

    # Send wrong OTP up to max attempts (3 times)
    for i in range(3):
        resp_err = client.post("/api/parent/verify-otp", json={
            "roll_number": student_id,
            "mobile_number": phone,
            "otp": "000000"
        })
        assert resp_err.status_code == 400

    # 4th attempt is locked out
    resp_locked = client.post("/api/parent/verify-otp", json={
        "roll_number": student_id,
        "mobile_number": phone,
        "otp": valid_otp or "123456"
    })
    assert resp_locked.status_code == 400
    assert "Too many failed verification attempts" in resp_locked.json()["detail"]

def test_otp_successful_verification_and_child_access(client, db_session, student_user_and_token):
    student_user, _ = student_user_and_token
    student_id = student_user.id
    phone = "9876500003"

    db_session.query(ParentOTP).filter(ParentOTP.mobile_number == phone).delete()
    parent = db_session.query(Parent).filter(Parent.student_id == student_id).first()
    if not parent:
        parent = Parent(student_id=student_id, parent_name="Valid Guardian", mobile_number=phone)
        db_session.add(parent)
    else:
        parent.mobile_number = phone
    db_session.commit()

    resp_req = client.post("/api/parent/request-otp", json={
        "roll_number": student_id,
        "mobile_number": phone
    })
    assert resp_req.status_code == 200
    assert "otp_debug" not in resp_req.json()
    otp = getattr(sms_provider, "last_dispatched_otp", {}).get(phone)
    assert otp is not None

    # Verify with correct OTP
    resp_verify = client.post("/api/parent/verify-otp", json={
        "roll_number": student_id,
        "mobile_number": phone,
        "otp": otp
    })
    assert resp_verify.status_code == 200
    auth_data = resp_verify.json()
    assert "access_token" in auth_data
    assert auth_data["role"] == "parent"

    # Access child dashboard with parent token
    headers = {"Authorization": f"Bearer {auth_data['access_token']}"}
    resp_child = client.get("/api/parent/child", headers=headers)
    assert resp_child.status_code == 200
    child_data = resp_child.json()
    assert child_data["student"]["id"] == student_id
