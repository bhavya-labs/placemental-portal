import pytest
import json
from backend.app.models import Student
from backend.app.ml.predictor import predictor

def test_readiness_ideal_profile():
    # 30% academics + 30% skills/certs + 25% projects + 15% coding = 100.0
    student = Student(
        cgpa=10.0,
        attendance=100.0,
        backlogs=0,
        skills=json.dumps(["Python", "Java", "C++", "SQL", "Docker", "Git", "React"]),
        certifications=json.dumps(["AWS", "GCP"]),
        projects=json.dumps([{"title": "P1"}, {"title": "P2"}, {"title": "P3"}]),
        leetcode_score=250,
        codechef_score=150,
        hackerrank_score=100
    )
    score = predictor.calculate_readiness_score(student)
    assert score == 100.0

def test_readiness_zero_profile():
    student = Student(
        cgpa=0.0,
        attendance=0.0,
        backlogs=0,
        skills=json.dumps([]),
        certifications=json.dumps([]),
        projects=json.dumps([]),
        leetcode_score=0,
        codechef_score=0,
        hackerrank_score=0
    )
    score = predictor.calculate_readiness_score(student)
    assert score == 0.0

def test_readiness_negative_bound_clamping():
    # Student with severe backlogs: academic_comp should clamp to 0.0, not negative
    student = Student(
        cgpa=2.0,            # min(2/10*20, 20) = 4.0
        attendance=20.0,      # min(20/100*10, 10) = 2.0
        backlogs=10,          # 10 * 3 = 30 penalty -> 4 + 2 - 30 = -24 -> clamped to 0.0
        skills=json.dumps([]),
        certifications=json.dumps([]),
        projects=json.dumps([]),
        leetcode_score=0,
        codechef_score=0,
        hackerrank_score=0
    )
    score = predictor.calculate_readiness_score(student)
    assert score == 0.0
    assert isinstance(score, float)

def test_readiness_over_bound_clamping():
    # Values exceeding individual component maximums
    student = Student(
        cgpa=10.0,
        attendance=100.0,
        backlogs=0,
        skills=json.dumps([f"Skill_{i}" for i in range(50)]),
        certifications=json.dumps([f"Cert_{i}" for i in range(20)]),
        projects=json.dumps([{"title": f"Project_{i}"} for i in range(15)]),
        leetcode_score=5000,
        codechef_score=5000,
        hackerrank_score=5000
    )
    score = predictor.calculate_readiness_score(student)
    assert score == 100.0

def test_readiness_intermediate_known_calculation():
    # CGPA: 8.0 -> 8.0/10*20 = 16.0
    # Attendance: 80.0% -> 80/100*10 = 8.0
    # Backlogs: 1 -> 1 * 3 = 3.0 penalty
    # Academic: 16.0 + 8.0 - 3.0 = 21.0
    # Skills: 3 skills -> 3 * 3.0 = 9.0
    # Certs: 1 cert -> 1 * 5.0 = 5.0
    # Skills comp: 9.0 + 5.0 = 14.0
    # Projects: 1 project -> 1 * 10.0 = 10.0
    # Coding: leetcode=100 -> (100 / 500) * 15.0 = 3.0
    # Expected total: 21.0 + 14.0 + 10.0 + 3.0 = 48.0
    student = Student(
        cgpa=8.0,
        attendance=80.0,
        backlogs=1,
        skills=json.dumps(["Python", "SQL", "Git"]),
        certifications=json.dumps(["AWS Practitioner"]),
        projects=json.dumps([{"title": "Web App"}]),
        leetcode_score=100,
        codechef_score=0,
        hackerrank_score=0
    )
    score = predictor.calculate_readiness_score(student)
    assert score == 48.0
