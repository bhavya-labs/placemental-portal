import pytest
from datetime import datetime, date, timedelta, timezone
from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from backend.app.models import (
    Base, User, Student, Faculty, Department, Company, PlacementDrive, 
    Application, CorrectionRequest, Permission
)
from backend.app.schemas import (
    CorrectionRequestCreate, CorrectionRequestAction, PlacementDriveCreate
)
from backend.app.routers.companies import (
    get_drives, get_drive_details, build_dept_filter, parse_date_param,
    get_ist_date, STATUS_REGISTRATION_OPEN, STATUS_REGISTRATION_CLOSED,
    STATUS_DRAFT, STATUS_ARCHIVED
)
from backend.app.routers.students import (
    get_correction_requests, action_correction_request, create_correction_request
)

@pytest.fixture(scope="module")
def isolated_db():
    engine = create_engine("sqlite:///:memory:", echo=False, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Seed Departments
    cse = Department(id=1, name="Computer Science & Engineering", code="CSE")
    ece = Department(id=2, name="Electronics & Communication", code="ECE")
    it = Department(id=3, name="Information Technology", code="IT")
    civil = Department(id=4, name="Civil Engineering", code="CIVIL")
    session.add_all([cse, ece, it, civil])
    session.commit()

    # Seed Users
    admin_u = User(id=1, email="admin@college.edu", name="System Administrator", role="admin", password_hash="hash")
    tnp_u = User(id=2, email="tnp@college.edu", name="Placement Officer", role="tnp", password_hash="hash")
    
    # Faculty User - CSE Dept
    fac_cse_u = User(id=3, email="faculty_cse@college.edu", name="Prof. CSE", role="faculty", password_hash="hash")
    # Faculty User - ECE Dept
    fac_ece_u = User(id=4, email="faculty_ece@college.edu", name="Prof. ECE", role="faculty", password_hash="hash")
    # Faculty User - All Scope
    fac_all_u = User(id=5, email="faculty_all@college.edu", name="Prof. Dean", role="faculty", password_hash="hash")

    # Students
    std_cse_u = User(id=6, email="student_cse@college.edu", name="Rajesh Kumar", role="student", password_hash="hash")
    std_ece_u = User(id=7, email="student_ece@college.edu", name="Priya Sen", role="student", password_hash="hash")

    session.add_all([admin_u, tnp_u, fac_cse_u, fac_ece_u, fac_all_u, std_cse_u, std_ece_u])
    session.commit()

    # Faculty Profiles
    fac_cse_prof = Faculty(id=3, dept_id=1, designation="Associate Professor")
    fac_ece_prof = Faculty(id=4, dept_id=2, designation="Assistant Professor")
    fac_all_prof = Faculty(id=5, dept_id=1, designation="Professor & Dean")
    session.add_all([fac_cse_prof, fac_ece_prof, fac_all_prof])
    session.commit()

    # Permissions
    now = datetime.utcnow()
    p_cse = Permission(
        user_id=3, module="Placement Drives", action="VIEW", scope="DEPARTMENT",
        scope_value="CSE", status="Active", start_date=now - timedelta(days=1),
        expiry_date=now + timedelta(days=365)
    )
    p_ece = Permission(
        user_id=4, module="Placement Drives", action="VIEW", scope="DEPARTMENT",
        scope_value="ECE", status="Active", start_date=now - timedelta(days=1),
        expiry_date=now + timedelta(days=365)
    )
    p_all = Permission(
        user_id=5, module="Placement Drives", action="VIEW", scope="ALL",
        scope_value=None, status="Active", start_date=now - timedelta(days=1),
        expiry_date=now + timedelta(days=365)
    )
    session.add_all([p_cse, p_ece, p_all])
    session.commit()

    # Student Profiles
    s_cse = Student(
        id=6, dept_id=1, gender="Male", batch="2026", section="A",
        phone="9876543201", cgpa=8.5, backlogs=0, attendance=85.0,
        status="Unplaced", skills='["Python", "Django"]'
    )
    s_ece = Student(
        id=7, dept_id=2, gender="Female", batch="2026", section="B",
        phone="9876543202", cgpa=7.5, backlogs=1, attendance=78.0,
        status="Unplaced", skills='["VLSI", "C++"]'
    )
    session.add_all([s_cse, s_ece])
    session.commit()

    # Companies
    c1 = Company(id=1, name="AlphaCorp Technologies", industry="IT", website="https://alpha.example.com")
    c2 = Company(id=2, name="Beta Systems Ltd", industry="Electronics", website="https://beta.example.com")
    c3 = Company(id=3, name="CivilInfra Builders", industry="Construction", website="https://infra.example.com")
    session.add_all([c1, c2, c3])
    session.commit()

    return {
        "session": session,
        "admin": admin_u,
        "tnp": tnp_u,
        "fac_cse": fac_cse_u,
        "fac_ece": fac_ece_u,
        "fac_all": fac_all_u,
        "std_cse": std_cse_u,
        "std_ece": std_ece_u,
        "student_cse_profile": s_cse,
        "student_ece_profile": s_ece,
    }


# ============================================================================
# 1. CORRECTION REQUESTS TESTS
# ============================================================================

def test_correction_requests_pagination_and_clamping(isolated_db):
    session = isolated_db["session"]
    admin = isolated_db["admin"]
    std_cse = isolated_db["std_cse"]

    # Clear prior correction requests
    session.query(CorrectionRequest).delete()
    session.commit()

    # Seed 5 correction requests
    fields = ["CGPA", "Attendance", "Backlogs", "Name", "Section"]
    for i, f in enumerate(fields, start=1):
        req = CorrectionRequest(
            id=100 + i,
            student_id=std_cse.id,
            field=f,
            current_value=f"Old_{f}",
            requested_value=f"New_{f}",
            reason=f"Correction for semester {i}",
            status="Pending",
            created_at=datetime.utcnow() - timedelta(minutes=10 * i)
        )
        session.add(req)
    session.commit()

    # Test pagination: page=1, limit=2
    res_p1 = get_correction_requests(page=1, limit=2, current_user=admin, db=session)
    assert len(res_p1) == 2
    assert res_p1[0].field == "CGPA"
    assert res_p1[1].field == "Attendance"

    # Test pagination: page=2, limit=2
    res_p2 = get_correction_requests(page=2, limit=2, current_user=admin, db=session)
    assert len(res_p2) == 2
    assert res_p2[0].field == "Backlogs"
    assert res_p2[1].field == "Name"

    # Test pagination: page=3, limit=2 (only 1 remaining)
    res_p3 = get_correction_requests(page=3, limit=2, current_user=admin, db=session)
    assert len(res_p3) == 1
    assert res_p3[0].field == "Section"

    # Test clamping: negative/zero page clamped safely to page 1
    res_clamped = get_correction_requests(page=-5, limit=2, current_user=admin, db=session)
    assert len(res_clamped) == 2
    assert res_clamped[0].field == "CGPA"

    # Test oversized limit clamped to max 100
    res_all = get_correction_requests(page=1, limit=500, current_user=admin, db=session)
    assert len(res_all) == 5


def test_correction_requests_approval_rejection_workflows(isolated_db):
    session = isolated_db["session"]
    admin = isolated_db["admin"]
    std_cse = isolated_db["std_cse"]
    std_profile = isolated_db["student_cse_profile"]

    # 1. Create a CGPA correction request
    req1 = CorrectionRequest(
        id=201,
        student_id=std_cse.id,
        field="CGPA",
        current_value="8.5",
        requested_value="9.2",
        reason="Updated grade sheet issued by university",
        status="Pending"
    )
    session.add(req1)
    session.commit()

    # Admin approves CGPA update
    res1 = action_correction_request(
        request_id=201,
        action_data=CorrectionRequestAction(status="Approved"),
        current_user=admin,
        db=session
    )
    assert "Approved" in res1["message"]
    session.refresh(req1)
    assert req1.status == "Approved"
    session.refresh(std_profile)
    assert std_profile.cgpa == 9.2

    # 2. Create a Name correction request
    req2 = CorrectionRequest(
        id=202,
        student_id=std_cse.id,
        field="Name",
        current_value="Rajesh Kumar",
        requested_value="Rajesh K. Sharma",
        reason="Official Aadhaar passport alignment",
        status="Pending"
    )
    session.add(req2)
    session.commit()

    # Admin rejects request
    res2 = action_correction_request(
        request_id=202,
        action_data=CorrectionRequestAction(status="Rejected"),
        current_user=admin,
        db=session
    )
    assert "Rejected" in res2["message"]
    session.refresh(req2)
    assert req2.status == "Rejected"
    session.refresh(std_cse)
    assert std_cse.name == "Rajesh Kumar"  # Name remains unchanged on rejection

    # Non-admin cannot action requests
    with pytest.raises(HTTPException) as exc_info:
        action_correction_request(
            request_id=201,
            action_data=CorrectionRequestAction(status="Approved"),
            current_user=std_cse,
            db=session
        )
    assert exc_info.value.status_code == 403


# ============================================================================
# 2. PLACEMENT DRIVE SEARCH TESTS
# ============================================================================

def test_drive_search_by_company_role_and_job_id(isolated_db):
    session = isolated_db["session"]
    admin = isolated_db["admin"]
    today = get_ist_date()

    # Clean existing drives
    session.query(PlacementDrive).delete()
    session.commit()

    d1 = PlacementDrive(
        id=301, company_id=1, role="Full Stack Developer", package_lpa=10.0,
        location="Hyderabad", cgpa_cutoff=7.0, allowed_depts="CSE,ECE",
        interview_date=today + timedelta(days=10), deadline=today + timedelta(days=5),
        status="REGISTRATION_OPEN", job_id="JOB-FS-301", batch="2026"
    )
    d2 = PlacementDrive(
        id=302, company_id=2, role="Embedded Systems Engineer", package_lpa=8.5,
        location="Bengaluru", cgpa_cutoff=6.5, allowed_depts="ECE",
        interview_date=today + timedelta(days=12), deadline=today + timedelta(days=6),
        status="REGISTRATION_OPEN", job_id="JOB-EMB-302", batch="2026"
    )
    d3 = PlacementDrive(
        id=303, company_id=3, role="Infrastructure QA Specialist", package_lpa=6.0,
        location="Chennai", cgpa_cutoff=6.0, allowed_depts="ALL",
        interview_date=today + timedelta(days=15), deadline=today + timedelta(days=8),
        status="REGISTRATION_OPEN", job_id="JOB-QA-303", batch="2026"
    )
    session.add_all([d1, d2, d3])
    session.commit()

    # 1. Search by Company Name (case-insensitive partial: "alphacorp")
    res_comp = get_drives(search="alphacorp", current_user=admin, db=session)
    assert len(res_comp) == 1
    assert res_comp[0]["id"] == 301
    assert res_comp[0]["company_name"] == "AlphaCorp Technologies"

    # 2. Search by Role (case-insensitive partial: "Embedded")
    res_role = get_drives(search="embedded", current_user=admin, db=session)
    assert len(res_role) == 1
    assert res_role[0]["id"] == 302
    assert res_role[0]["role"] == "Embedded Systems Engineer"

    # 3. Search by Job ID (exact/partial: "JOB-QA")
    res_job_id = get_drives(search="JOB-QA-303", current_user=admin, db=session)
    assert len(res_job_id) == 1
    assert res_job_id[0]["id"] == 303
    assert res_job_id[0]["job_id"] == "JOB-QA-303"

    # 4. Empty/whitespace search returns all non-archived drives safely
    res_empty = get_drives(search="   ", current_user=admin, db=session)
    assert len(res_empty) == 3

    # 5. SQL injection safety check
    res_sqli = get_drives(search="' OR '1'='1", current_user=admin, db=session)
    assert len(res_sqli) == 0  # Safely returns 0 matches, does not inject or crash


# ============================================================================
# 3. PLACEMENT DRIVE FILTER TESTS (DEPARTMENT EXACT BOUNDARY)
# ============================================================================

def test_drive_department_exact_boundary_filtering(isolated_db):
    """
    CRITICAL: Verify exact boundary department matching.
    'IT' must NOT match 'CIVIL'.
    'CE' must NOT match 'ECE'.
    'ALL' matches all departments.
    """
    session = isolated_db["session"]
    admin = isolated_db["admin"]
    today = get_ist_date()

    session.query(PlacementDrive).delete()
    session.commit()

    # Seed drives with tricky department configurations
    # Drive 401: CSE,ECE
    d_cse_ece = PlacementDrive(
        id=401, company_id=1, role="Software Engineer", package_lpa=8.0,
        allowed_depts="CSE,ECE", location="Hyderabad", cgpa_cutoff=7.0,
        interview_date=today + timedelta(days=10), deadline=today + timedelta(days=5),
        status="REGISTRATION_OPEN", batch="2026"
    )
    # Drive 402: CIVIL (contains substring 'I' and 'T' or 'IL' - must NOT match 'IT')
    d_civil = PlacementDrive(
        id=402, company_id=3, role="Site Engineer", package_lpa=6.0,
        allowed_depts="CIVIL", location="Hyderabad", cgpa_cutoff=6.0,
        interview_date=today + timedelta(days=10), deadline=today + timedelta(days=5),
        status="REGISTRATION_OPEN", batch="2026"
    )
    # Drive 403: IT alone
    d_it = PlacementDrive(
        id=403, company_id=1, role="IT Systems Analyst", package_lpa=7.5,
        allowed_depts="IT", location="Bengaluru", cgpa_cutoff=6.5,
        interview_date=today + timedelta(days=10), deadline=today + timedelta(days=5),
        status="REGISTRATION_OPEN", batch="2026"
    )
    # Drive 404: CSE, IT, ECE (spaced list)
    d_multi = PlacementDrive(
        id=404, company_id=2, role="Cloud Developer", package_lpa=11.0,
        allowed_depts="CSE, IT, ECE", location="Pune", cgpa_cutoff=7.5,
        interview_date=today + timedelta(days=10), deadline=today + timedelta(days=5),
        status="REGISTRATION_OPEN", batch="2026"
    )
    # Drive 405: ALL
    d_all = PlacementDrive(
        id=405, company_id=1, role="Management Trainee", package_lpa=9.0,
        allowed_depts="ALL", location="Mumbai", cgpa_cutoff=6.0,
        interview_date=today + timedelta(days=10), deadline=today + timedelta(days=5),
        status="REGISTRATION_OPEN", batch="2026"
    )
    # Drive 406: ECE alone (must NOT match 'CE')
    d_ece = PlacementDrive(
        id=406, company_id=2, role="Hardware Designer", package_lpa=8.5,
        allowed_depts="ECE", location="Chennai", cgpa_cutoff=7.0,
        interview_date=today + timedelta(days=10), deadline=today + timedelta(days=5),
        status="REGISTRATION_OPEN", batch="2026"
    )
    session.add_all([d_cse_ece, d_civil, d_it, d_multi, d_all, d_ece])
    session.commit()

    # 1. Filter by IT: Must match IT (403), CSE, IT, ECE (404), ALL (405).
    # MUST NOT match CIVIL (402)!
    res_it = get_drives(dept="IT", current_user=admin, db=session)
    matched_it_ids = {d["id"] for d in res_it}
    assert 403 in matched_it_ids, "Drive 403 (IT) must match"
    assert 404 in matched_it_ids, "Drive 404 (CSE, IT, ECE) must match"
    assert 405 in matched_it_ids, "Drive 405 (ALL) must match"
    assert 402 not in matched_it_ids, "Drive 402 (CIVIL) must NOT match IT!"
    assert 401 not in matched_it_ids, "Drive 401 (CSE,ECE) must NOT match IT!"
    assert 406 not in matched_it_ids, "Drive 406 (ECE) must NOT match IT!"

    # 2. Filter by CE: Must NOT match ECE (401, 404, 406)
    res_ce = get_drives(dept="CE", current_user=admin, db=session)
    matched_ce_ids = {d["id"] for d in res_ce}
    assert 405 in matched_ce_ids, "Drive 405 (ALL) must match"
    assert 406 not in matched_ce_ids, "Drive 406 (ECE) must NOT match CE!"
    assert 401 not in matched_ce_ids, "Drive 401 (CSE,ECE) must NOT match CE!"

    # 3. Filter by CIVIL: Must match CIVIL (402) and ALL (405)
    res_civil = get_drives(dept="CIVIL", current_user=admin, db=session)
    matched_civil_ids = {d["id"] for d in res_civil}
    assert 402 in matched_civil_ids
    assert 405 in matched_civil_ids
    assert 403 not in matched_civil_ids


# ============================================================================
# 4. PLACEMENT DRIVE FILTERS: LOCATION, REG STATUS, DATE RANGE
# ============================================================================

def test_drive_location_and_reg_status_filters(isolated_db):
    session = isolated_db["session"]
    admin = isolated_db["admin"]
    today = get_ist_date()

    session.query(PlacementDrive).delete()
    session.commit()

    # Drive 1: Open, Hyderabad
    d1 = PlacementDrive(
        id=501, company_id=1, role="DevOps Engineer", package_lpa=12.0,
        location="Hyderabad, Telangana", allowed_depts="ALL",
        interview_date=today + timedelta(days=10), deadline=today + timedelta(days=3),
        status="REGISTRATION_OPEN", batch="2026"
    )
    # Drive 2: Closed (Deadline expired), Hyderabad
    d2 = PlacementDrive(
        id=502, company_id=1, role="Security Analyst", package_lpa=10.0,
        location="Hyderabad", allowed_depts="ALL",
        interview_date=today + timedelta(days=10), deadline=today - timedelta(days=1),
        status="REGISTRATION_OPEN", batch="2026"
    )
    # Drive 3: Open, Bengaluru
    d3 = PlacementDrive(
        id=503, company_id=2, role="Data Scientist", package_lpa=15.0,
        location="Bengaluru", allowed_depts="ALL",
        interview_date=today + timedelta(days=15), deadline=today + timedelta(days=5),
        status="REGISTRATION_OPEN", batch="2026"
    )
    # Drive 4: Explicit REGISTRATION_CLOSED, Pune
    d4 = PlacementDrive(
        id=504, company_id=2, role="QA Automation", package_lpa=7.0,
        location="Pune", allowed_depts="ALL",
        interview_date=today + timedelta(days=5), deadline=today - timedelta(days=2),
        status="REGISTRATION_CLOSED", batch="2026"
    )
    session.add_all([d1, d2, d3, d4])
    session.commit()

    # 1. Location filter (partial, case-insensitive)
    res_hyd = get_drives(location="hyderabad", current_user=admin, db=session)
    assert len(res_hyd) == 2
    assert {d["id"] for d in res_hyd} == {501, 502}

    # 2. Registration status filter = OPEN
    res_open = get_drives(reg_status="OPEN", current_user=admin, db=session)
    assert {d["id"] for d in res_open} == {501, 503}

    # 3. Registration status filter = CLOSED
    res_closed = get_drives(reg_status="CLOSED", current_user=admin, db=session)
    assert {d["id"] for d in res_closed} == {502, 504}


def test_drive_date_range_filtering(isolated_db):
    session = isolated_db["session"]
    admin = isolated_db["admin"]

    session.query(PlacementDrive).delete()
    session.commit()

    d1 = PlacementDrive(
        id=601, company_id=1, role="Engineer Oct 05", package_lpa=8.0,
        location="Hyd", allowed_depts="ALL",
        interview_date=date(2026, 10, 5), deadline=date(2026, 9, 30),
        status="REGISTRATION_OPEN", batch="2026"
    )
    d2 = PlacementDrive(
        id=602, company_id=1, role="Engineer Oct 15", package_lpa=8.0,
        location="Hyd", allowed_depts="ALL",
        interview_date=date(2026, 10, 15), deadline=date(2026, 10, 10),
        status="REGISTRATION_OPEN", batch="2026"
    )
    d3 = PlacementDrive(
        id=603, company_id=1, role="Engineer Oct 25", package_lpa=8.0,
        location="Hyd", allowed_depts="ALL",
        interview_date=date(2026, 10, 25), deadline=date(2026, 10, 20),
        status="REGISTRATION_OPEN", batch="2026"
    )
    session.add_all([d1, d2, d3])
    session.commit()

    # 1. date_from filter only
    res_from = get_drives(date_from="2026-10-10", current_user=admin, db=session)
    assert {d["id"] for d in res_from} == {602, 603}

    # 2. date_to filter only
    res_to = get_drives(date_to="2026-10-20", current_user=admin, db=session)
    assert {d["id"] for d in res_to} == {601, 602}

    # 3. date_from and date_to bounded range
    res_range = get_drives(date_from="2026-10-10", date_to="2026-10-20", current_user=admin, db=session)
    assert {d["id"] for d in res_range} == {602}

    # 4. Invalid date strings don't crash
    res_safe = get_drives(date_from="invalid-date", current_user=admin, db=session)
    assert len(res_safe) == 3


# ============================================================================
# 5. PAGINATION AND BACKWARD COMPATIBILITY
# ============================================================================

def test_drive_pagination_metadata_and_clamping(isolated_db):
    session = isolated_db["session"]
    admin = isolated_db["admin"]
    today = get_ist_date()

    session.query(PlacementDrive).delete()
    session.commit()

    # Seed 12 drives
    drives = [
        PlacementDrive(
            id=700 + i, company_id=1, role=f"Role {i:02d}", package_lpa=7.0 + i,
            location="Hyderabad", allowed_depts="CSE",
            interview_date=today + timedelta(days=i), deadline=today + timedelta(days=i - 1),
            status="REGISTRATION_OPEN", batch="2026"
        )
        for i in range(1, 13)
    ]
    session.add_all(drives)
    session.commit()

    # 1. Unpaginated request (no page or size) returns plain List for backward compatibility
    res_plain = get_drives(current_user=admin, db=session)
    assert isinstance(res_plain, list)
    assert len(res_plain) == 12

    # 2. Paginated request returns dict with items, total, page, page_size, total_pages
    res_p1 = get_drives(page=1, page_size=5, current_user=admin, db=session)
    assert isinstance(res_p1, dict)
    assert res_p1["total"] == 12
    assert res_p1["page"] == 1
    assert res_p1["page_size"] == 5
    assert res_p1["total_pages"] == 3
    assert len(res_p1["items"]) == 5
    assert res_p1["items"][0]["id"] == 701

    # Page 2
    res_p2 = get_drives(page=2, page_size=5, current_user=admin, db=session)
    assert len(res_p2["items"]) == 5
    assert res_p2["items"][0]["id"] == 706

    # Page 3 (remaining 2)
    res_p3 = get_drives(page=3, page_size=5, current_user=admin, db=session)
    assert len(res_p3["items"]) == 2
    assert res_p3["items"][0]["id"] == 711

    # 3. Invalid/negative page clamping
    res_clamp_page = get_drives(page=-3, page_size=5, current_user=admin, db=session)
    assert res_clamp_page["page"] == 1
    assert len(res_clamp_page["items"]) == 5

    # 4. Limit parameter works as page_size alias and clamps to max 100
    res_clamp_limit = get_drives(page=1, limit=500, current_user=admin, db=session)
    assert res_clamp_limit["page_size"] == 100
    assert len(res_clamp_limit["items"]) == 12

    # 5. Empty results return empty array and 0 total_pages
    res_empty = get_drives(dept="CIVIL", page=1, page_size=5, current_user=admin, db=session)
    assert res_empty["total"] == 0
    assert res_empty["total_pages"] == 0
    assert res_empty["items"] == []


# ============================================================================
# 6. FACULTY & HOD DEPARTMENT RBAC AND SCOPE ISOLATION
# ============================================================================

def test_faculty_department_rbac_and_scope_isolation(isolated_db):
    session = isolated_db["session"]
    fac_cse = isolated_db["fac_cse"]
    fac_ece = isolated_db["fac_ece"]
    fac_all = isolated_db["fac_all"]
    today = get_ist_date()

    session.query(PlacementDrive).delete()
    session.commit()

    # Drive 801: CSE only
    d_cse = PlacementDrive(
        id=801, company_id=1, role="AI Research Intern", package_lpa=14.0,
        location="Hyderabad", allowed_depts="CSE",
        interview_date=today + timedelta(days=10), deadline=today + timedelta(days=5),
        status="REGISTRATION_OPEN", batch="2026"
    )
    # Drive 802: ECE only
    d_ece = PlacementDrive(
        id=802, company_id=2, role="Semiconductor Verification", package_lpa=12.0,
        location="Bengaluru", allowed_depts="ECE",
        interview_date=today + timedelta(days=12), deadline=today + timedelta(days=6),
        status="REGISTRATION_OPEN", batch="2026"
    )
    # Drive 803: ALL depts
    d_all = PlacementDrive(
        id=803, company_id=1, role="Analyst", package_lpa=9.0,
        location="Chennai", allowed_depts="ALL",
        interview_date=today + timedelta(days=15), deadline=today + timedelta(days=7),
        status="REGISTRATION_OPEN", batch="2026"
    )
    session.add_all([d_cse, d_ece, d_all])
    session.commit()

    # 1. Faculty with CSE scope in get_drives: sees CSE (801) and ALL (803).
    # MUST NOT see ECE drive (802)!
    res_cse = get_drives(current_user=fac_cse, db=session)
    cse_ids = {d["id"] for d in res_cse}
    assert 801 in cse_ids
    assert 803 in cse_ids
    assert 802 not in cse_ids, "Faculty with CSE scope must not see ECE drive in list"

    # 2. Faculty with ECE scope in get_drives: sees ECE (802) and ALL (803).
    # MUST NOT see CSE drive (801)!
    res_ece = get_drives(current_user=fac_ece, db=session)
    ece_ids = {d["id"] for d in res_ece}
    assert 802 in ece_ids
    assert 803 in ece_ids
    assert 801 not in ece_ids, "Faculty with ECE scope must not see CSE drive in list"

    # 3. Direct drive details inspection (/api/drives/{drive_id}):
    # Faculty with CSE scope inspecting CSE drive -> Success
    det_cse = get_drive_details(drive_id=801, current_user=fac_cse, db=session)
    assert det_cse["id"] == 801

    # Faculty with CSE scope inspecting ECE drive directly -> 403 Forbidden!
    with pytest.raises(HTTPException) as exc_info:
        get_drive_details(drive_id=802, current_user=fac_cse, db=session)
    assert exc_info.value.status_code == 403
    assert "outside authorized department scope" in exc_info.value.detail

    # 4. Faculty with ALL scope can view and inspect all drives
    res_all = get_drives(current_user=fac_all, db=session)
    assert len(res_all) == 3
    det_ece_all = get_drive_details(drive_id=802, current_user=fac_all, db=session)
    assert det_ece_all["id"] == 802


# ============================================================================
# 7. TAILWIND PURGE AND STATIC CSS INTEGRITY
# ============================================================================

def test_tailwind_static_classes_integrity():
    """
    Verify that frontend TSX files use complete static classes rather than dynamic interpolation
    like `col-span-${...}` which breaks Tailwind purge in production builds.
    """
    with open("frontend/src/pages/CorrectionRequests.tsx", "r", encoding="utf-8") as f:
        cr_content = f.read()

    assert "lg:col-span-${" not in cr_content, "Dynamic Tailwind interpolation detected in CorrectionRequests.tsx"
    assert "lg:col-span-3" in cr_content, "Static lg:col-span-3 class must be present"
    assert "lg:col-span-2" in cr_content, "Static lg:col-span-2 class must be present"
    assert "min-w-[700px]" in cr_content, "Responsive table minimum width must be specified"

    with open("frontend/src/pages/AdminDrives.tsx", "r", encoding="utf-8") as f:
        ad_content = f.read()

    assert "col-span-${" not in ad_content, "Dynamic Tailwind interpolation detected in AdminDrives.tsx"
    assert "Search by company name, job role, or Job ID" in ad_content
    assert "All Departments" in ad_content
    assert "Active Filters:" in ad_content
