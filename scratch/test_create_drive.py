import requests
import os

url_login = "http://127.0.0.1:8000/api/auth/login"
url_drives = "http://127.0.0.1:8000/api/drives"

# Get admin token
res = requests.post(url_login, json={"email": "admin@platform.edu", "password": "password123"})
print("Login status:", res.status_code)
token = res.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

payload = {
    "company_id": 1,
    "role": "QA Engineer",
    "package_lpa": 6.5,
    "location": "Hyderabad",
    "cgpa_cutoff": 7.0,
    "allowed_depts": "CSE,IT,ECE",
    "allowed_backlogs": 0,
    "bond_details": "No Bond",
    "selection_process": "Aptitude -> Technical -> HR",
    "interview_date": "2026-08-30",
    "deadline": "2026-08-28",
    "status": "Upcoming", # What status does the frontend send? Let's check both
    "job_id": "JD-QA-999",
    "responsibilities": "Test automation",
    "required_skills": "Python, Selenium",
    "preferred_skills": "Docker",
    "job_type": "Full-Time",
    "work_mode": "Onsite",
    "openings_count": 5,
    "hiring_process": "Online test -> Coding round -> HR",
    "company_logo": "https://logo.clearbit.com/google.com"
}

res2 = requests.post(url_drives, json=payload, headers=headers)
print("Create status:", res2.status_code)
print("Create response:", res2.text)
