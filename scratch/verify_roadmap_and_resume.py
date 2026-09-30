import sys
sys.path.insert(0, '.')
import json
import io
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.models import Student, PlacementDrive, User
from backend.app.ml.predictor import predictor
from backend.app.auth import create_access_token

def test_roadmaps():
    db = SessionLocal()
    try:
        student = db.query(Student).first()
        student_name = student.user.name if student.user else f"Student {student.id}"
        print(f"Testing with Student ID={student.id}, Name={student_name}, Skills={student.skills}")

        # 1. Drive 4 (Embedded Engineer)
        drive_embedded = db.query(PlacementDrive).filter(PlacementDrive.id == 4).first()
        # 2. Drive 6 (Data Analyst)
        drive_data = db.query(PlacementDrive).filter(PlacementDrive.id == 6).first()
        # 3. Drive 10 (Associate Software Engineer - Generic/Ambiguous)
        drive_generic = db.query(PlacementDrive).filter(PlacementDrive.id == 10).first()
        # 4. Drive 11 (Cloud Associate)
        drive_cloud = db.query(PlacementDrive).filter(PlacementDrive.id == 11).first()

        test_drives = [
            ("EMBEDDED DOMAIN", drive_embedded),
            ("DATA / ML DOMAIN", drive_data),
            ("GENERIC / AMBIGUOUS SWE DOMAIN", drive_generic),
            ("CLOUD / DEVOPS DOMAIN", drive_cloud)
        ]

        print("=" * 80)
        print("ROADMAP DOMAIN DIFFERENTIATION TEST")
        print("=" * 80)

        for label, drive in test_drives:
            if not drive:
                print(f"Drive not found for {label}")
                continue
            company_name = drive.company.name if drive.company else "Org"
            domain = predictor.classify_drive_domain(drive.role, drive.required_skills or "")
            roadmap = predictor.generate_preparation_roadmap(student, drive)
            
            print(f"\n--- [{label}] ---")
            print(f"Drive ID: {drive.id} | Company: {company_name} | Role: {drive.role}")
            print(f"Required Skills: {drive.required_skills}")
            print(f"Classified Technical Track: >>> {domain.upper()} <<<")
            for step in roadmap:
                print(f"  {step['week']}: {step['focus']}")
                for act in step['activities'][:2]:
                    print(f"    - {act}")
            print("-" * 60)

    finally:
        db.close()

def test_resume_upload():
    db = SessionLocal()
    try:
        student = db.query(Student).first()
        user = student.user
        token = create_access_token(data={"sub": user.email, "role": user.role.value if hasattr(user.role, 'value') else user.role, "id": user.id})

        client = TestClient(app)
        headers = {"Authorization": f"Bearer {token}"}

        sample_resume_content = b"""
        ALEX JOHNSON
        Software Developer
        Email: alex.johnson@example.com | Phone: +91 9876543210
        GitHub: https://github.com/alexjohnson | LinkedIn: https://linkedin.com/in/alexjohnson

        EDUCATION
        B.Tech in Computer Science and Engineering, CGPA: 8.4

        TECHNICAL SKILLS
        Programming Languages: Python, Java, JavaScript, SQL, C++
        Web & Frameworks: React, FastAPI, Node.js
        Data & Storage: PostgreSQL, MySQL, Redis
        Tools: Git, Docker, Linux

        EXPERIENCE & PROJECTS
        Full Stack Web Application:
        - Developed a responsive web portal using React and Python FastAPI with relational SQL queries.
        - Designed RESTful API endpoints and implemented authentication and data validation.
        """

        print("\n" + "=" * 80)
        print("RESUME UPLOAD TEST (WITH AND WITHOUT TARGET DRIVE)")
        print("=" * 80)

        # Case 1: Upload WITHOUT selecting a drive (Fallback to General Industry Software Baseline)
        files = {"file": ("alex_resume.pdf", sample_resume_content, "application/pdf")}
        res1 = client.post("/api/ai/resume/upload", files=files, headers=headers)
        print(f"\n[Case 1: No Drive Selected]")
        print(f"Status: {res1.status_code}")
        data1 = res1.json()
        print(f"Message: {data1.get('message')}")
        print(f"Comparison Target: >>> {data1.get('comparison_target')} <<<")
        print(f"Completeness Score: {data1.get('ats_score')}%")
        print(f"Skills Matched: {data1.get('analysis', {}).get('matching_skills')}")
        print(f"Missing Skills: {data1.get('analysis', {}).get('missing_skills')}")
        print(f"Suggestions: {data1.get('analysis', {}).get('improvement_tips')}")

        # Case 2: Upload WITH Drive 6 (Data Analyst - Python, Pandas, SQL, Scikit-Learn, Machine Learning)
        files = {"file": ("alex_resume.pdf", sample_resume_content, "application/pdf")}
        data_payload = {"drive_id": 6}
        res2 = client.post("/api/ai/resume/upload", files=files, data=data_payload, headers=headers)
        print(f"\n[Case 2: Selected Drive 6 (Infosys - Data Analyst)]")
        print(f"Status: {res2.status_code}")
        data2 = res2.json()
        print(f"Message: {data2.get('message')}")
        print(f"Comparison Target: >>> {data2.get('comparison_target')} <<<")
        print(f"Completeness Score: {data2.get('ats_score')}%")
        print(f"Skills Matched: {data2.get('analysis', {}).get('matching_skills')}")
        print(f"Missing Skills: {data2.get('analysis', {}).get('missing_skills')}")

        # Case 3: Upload WITH Drive 4 (Apple - Embedded Engineer - C, C++, Microcontrollers, RTOS, Assembly)
        files = {"file": ("alex_resume.pdf", sample_resume_content, "application/pdf")}
        data_payload = {"drive_id": 4}
        res3 = client.post("/api/ai/resume/upload", files=files, data=data_payload, headers=headers)
        print(f"\n[Case 3: Selected Drive 4 (Apple - Embedded Engineer)]")
        print(f"Status: {res3.status_code}")
        data3 = res3.json()
        print(f"Message: {data3.get('message')}")
        print(f"Comparison Target: >>> {data3.get('comparison_target')} <<<")
        print(f"Completeness Score: {data3.get('ats_score')}%")
        print(f"Skills Matched: {data3.get('analysis', {}).get('matching_skills')}")
        print(f"Missing Skills: {data3.get('analysis', {}).get('missing_skills')}")

    finally:
        db.close()

if __name__ == "__main__":
    test_roadmaps()
    test_resume_upload()
