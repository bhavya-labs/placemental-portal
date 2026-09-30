import os
import sys
import random
import json
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session
from backend.app.database import SessionLocal, Base, engine
from backend.app.models import Department, User, Student, Faculty, Company, PlacementDrive, Application, Interview, Feedback, Notification, SystemLog
from backend.app.auth import get_password_hash
from backend.app.ml.predictor import predictor
from backend.app.ml.nlp_feedback import nlp_analyzer

def seed_database():
    db = SessionLocal()
    try:
        print("Resetting database...")
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

        print("Creating departments...")
        depts_data = [
            {"name": "Computer Science & Engineering", "code": "CSE"},
            {"name": "Information Technology", "code": "IT"},
            {"name": "Electronics & Communication Engineering", "code": "ECE"},
            {"name": "Electrical & Electronics Engineering", "code": "EEE"},
            {"name": "Mechanical Engineering", "code": "MECH"},
            {"name": "Civil Engineering", "code": "CIVIL"}
        ]
        dept_objs = []
        for d in depts_data:
            dept = Department(name=d["name"], code=d["code"])
            db.add(dept)
            dept_objs.append(dept)
        db.commit()

        # Retrieve ids
        dept_ids = {d.code: d.id for d in dept_objs}

        # Generate a single password hash to reuse (saves 5-10 minutes of CPU time)
        print("Generating password hash...")
        shared_password_hash = get_password_hash("password123")

        print("Creating system administrative and coordinator accounts...")
        # 1 Admin
        admin_user = User(
            email="admin@platform.edu",
            password_hash=shared_password_hash,
            name="Dr. Aruna Kumar (Admin)",
            role="admin"
        )
        db.add(admin_user)

        # Faculty Placement Coordinators (1 per dept)
        faculty_users = []
        faculty_profiles = []
        dept_coordinators = [
            ("CSE", "Dr. Rajesh Sharma"),
            ("IT", "Prof. Sneha Reddy"),
            ("ECE", "Dr. M. K. Murthy"),
            ("EEE", "Prof. Ramana Rao"),
            ("MECH", "Dr. Satish Kumar"),
            ("CIVIL", "Prof. Venkat Prasad")
        ]
        
        for dept_code, name in dept_coordinators:
            f_user = User(
                email=f"faculty.{dept_code.lower()}@platform.edu",
                password_hash=shared_password_hash,
                name=f"{name} ({dept_code} Placement Officer)",
                role="faculty"
            )
            db.add(f_user)
            faculty_users.append(f_user)
            
        db.commit()

        # Create profiles
        for i, (dept_code, _) in enumerate(dept_coordinators):
            f_profile = Faculty(
                id=faculty_users[i].id,
                dept_id=dept_ids[dept_code],
                designation="Department Placement Coordinator"
            )
            db.add(f_profile)
        db.commit()

        print("Generating 150+ Companies...")
        companies_data = []
        industries = ["Software/IT", "Product Tech", "Consulting", "Finance/Banking", "Semiconductors", "Infrastructure/Core"]
        company_names = [
            ("Google", "Product Tech", "https://google.com"),
            ("Microsoft", "Product Tech", "https://microsoft.com"),
            ("Amazon", "Product Tech", "https://amazon.in"),
            ("Meta", "Product Tech", "https://meta.com"),
            ("Apple", "Product Tech", "https://apple.com"),
            ("TCS", "Software/IT", "https://tcs.com"),
            ("Infosys", "Software/IT", "https://infosys.com"),
            ("Wipro", "Software/IT", "https://wipro.com"),
            ("Cognizant", "Software/IT", "https://cognizant.com"),
            ("Accenture", "Consulting", "https://accenture.com"),
            ("Deloitte", "Consulting", "https://deloitte.com"),
            ("PwC", "Consulting", "https://pwc.com"),
            ("EY", "Consulting", "https://ey.com"),
            ("KPMG", "Consulting", "https://kpmg.com"),
            ("JP Morgan Chase", "Finance/Banking", "https://jpmorganchase.com"),
            ("Goldman Sachs", "Finance/Banking", "https://goldmansachs.com"),
            ("Morgan Stanley", "Finance/Banking", "https://morganstanley.com"),
            ("HDFC Bank", "Finance/Banking", "https://hdfcbank.com"),
            ("ICICI Bank", "Finance/Banking", "https://icicibank.com"),
            ("Intel", "Semiconductors", "https://intel.com"),
            ("NVIDIA", "Product Tech", "https://nvidia.com"),
            ("Qualcomm", "Semiconductors", "https://qualcomm.com"),
            ("AMD", "Semiconductors", "https://amd.com"),
            ("Texas Instruments", "Semiconductors", "https://ti.com"),
            ("L&T Construction", "Infrastructure/Core", "https://larsentoubro.com"),
            ("Tata Motors", "Infrastructure/Core", "https://tatamotors.com"),
            ("Mahindra & Mahindra", "Infrastructure/Core", "https://mahindra.com"),
            ("Reliance Industries", "Infrastructure/Core", "https://ril.com"),
            ("Adani Group", "Infrastructure/Core", "https://adani.com"),
            ("Cisco", "Product Tech", "https://cisco.com"),
            ("Oracle", "Product Tech", "https://oracle.com"),
            ("Salesforce", "Product Tech", "https://salesforce.com"),
            ("Adobe", "Product Tech", "https://adobe.com"),
            ("ServiceNow", "Product Tech", "https://servicenow.com"),
            ("Atlassian", "Product Tech", "https://atlassian.com"),
            ("Uber", "Product Tech", "https://uber.com"),
            ("Ola", "Product Tech", "https://ola.in"),
            ("Flipkart", "Product Tech", "https://flipkart.com"),
            ("Paytm", "Finance/Banking", "https://paytm.com"),
            ("PhonePe", "Finance/Banking", "https://phonepe.com")
        ]

        # Generate up to 155 companies
        for i in range(1, 156):
            if i <= len(company_names):
                name, industry, web = company_names[i-1]
            else:
                name = f"TechCorp Solutions {i}"
                industry = random.choice(industries)
                web = f"https://techcorp{i}.com"
            companies_data.append(Company(
                name=name,
                industry=industry,
                website=web,
                description=f"Leading organization providing top-tier solutions in {industry}."
            ))
        db.add_all(companies_data)
        db.commit()

        # Retrieve companies
        companies = db.query(Company).all()

        print("Generating 3,000 Students...")
        skills_pool = {
            "CSE": ["Python", "Java", "SQL", "React", "JavaScript", "C++", "Docker", "AWS", "Data Structures", "Algorithms", "Git"],
            "IT": ["JavaScript", "HTML", "CSS", "React", "Node.js", "Express", "MongoDB", "SQL", "Python", "Git"],
            "ECE": ["Python", "C", "Embedded Systems", "Verilog", "MATLAB", "SQL", "IoT", "Microcontrollers", "Data Structures"],
            "EEE": ["MATLAB", "Power Systems", "Circuit Design", "IoT", "Python", "SQL", "PLC Programming"],
            "MECH": ["AutoCAD", "SolidWorks", "Ansys", "Python", "SQL", "Project Management", "Thermodynamics"],
            "CIVIL": ["AutoCAD", "STAAD Pro", "Revit", "Project Management", "SQL", "Estimation"]
        }

        names_pool = [
            "Rahul", "Priya", "Amit", "Sneha", "Kiran", "Divya", "Sanjay", "Anjali", "Vikram", "Deepika",
            "Vijay", "Harini", "Sandeep", "Swathi", "Manish", "Kavya", "Rohan", "Archana", "Karthik", "Ramya",
            "Venkatesh", "Jyothi", "Naveen", "Bhavana", "Sai", "Lakshmi", "Harish", "Sindhu", "Prasad", "Sravani",
            "Rajesh", "Asha", "Satish", "Uma", "Naresh", "Pallavi", "Ravi", "Sandhya", "Mahesh", "Geetha",
            "Srinivas", "Latha", "Krishna", "Radha", "Gopal", "Saraswathi", "Ramesh", "Sujatha", "Pradeep", "Divya"
        ]
        surnames_pool = ["Goud", "Reddy", "Rao", "Naidu", "Chowdary", "Sharma", "Verma", "Patel", "Singh", "Joshi", "Bhatt", "Nair", "Pillai", "Kumar", "Prasad"]

        batches = ["2026", "2025"]  # 2026 (current active), 2025 (graduated, used for training history)
        genders = ["Male", "Female"]

        # Insert Users and Students in chunks to keep memory usage low and fast database commits
        user_inserts = []
        student_inserts = []
        
        # Prepare list of attributes
        student_tuples = []
        
        # We need 3,000 students
        for j in range(1, 3001):
            gender = random.choice(genders)
            first_name = random.choice(names_pool)
            last_name = random.choice(surnames_pool)
            name = f"{first_name} {last_name}"
            
            # Balance departments
            dept_code = random.choice(["CSE", "IT", "ECE", "EEE", "MECH", "CIVIL"])
            # Distribute CGPAs realistically (mean 7.5, std 1.0)
            cgpa = round(min(10.0, max(4.0, random.normalvariate(7.6, 1.1))), 2)
            # Higher CGPA gets higher coding scores and more skills
            
            # Backlog distribution: 92% have 0, others 1-3
            backlogs = 0
            if random.random() > 0.92:
                backlogs = random.choice([1, 2, 3])
                
            attendance = round(random.uniform(65.0, 98.0), 1)
            
            # Select skills based on department and CGPA
            dept_skills = skills_pool[dept_code]
            num_skills = min(len(dept_skills), int(cgpa * 0.8) + random.randint(1, 3))
            selected_skills = random.sample(dept_skills, min(num_skills, len(dept_skills)))
            
            # Projects
            projects = []
            num_projects = 1 if cgpa < 6.5 else (2 if cgpa < 8.5 else 3)
            for p_idx in range(1, num_projects + 1):
                projects.append({
                    "title": f"{dept_code} Project {p_idx}",
                    "description": f"Developed an advanced {dept_code} related project using key concepts.",
                    "skills_used": random.sample(selected_skills, min(3, len(selected_skills))) if selected_skills else []
                })
                
            # Certifications
            certs = []
            if cgpa >= 7.0:
                certs.append({
                    "name": f"Certified {dept_code} Professional",
                    "issuer": "Coursera / Udemy",
                    "date_obtained": "2025-06-15"
                })
            if cgpa >= 8.5 and random.random() > 0.5:
                certs.append({
                    "name": "AWS Cloud Practitioner",
                    "issuer": "Amazon Web Services",
                    "date_obtained": "2025-11-20"
                })

            # Coding scores (Higher for CSE/IT)
            multiplier = 1.5 if dept_code in ["CSE", "IT"] else 0.6
            leetcode = int(max(0, random.normalvariate(180, 100) * multiplier * (cgpa / 7.5)))
            codechef = int(max(0, leetcode * 0.9 + random.randint(-50, 50)))
            hackerrank = int(max(0, leetcode * 1.2 + random.randint(-50, 50)))

            batch = "2026" if j <= 2000 else "2025"  # 2000 current students, 1000 past student records
            
            # Placement status
            # For past batch (2025), assign Placed/Unplaced. For 2026, set Placed if selected, default Unplaced.
            status = "Unplaced"
            if batch == "2025":
                status = "Placed" if (cgpa >= 6.5 and backlogs == 0 and random.random() > 0.25) else "Unplaced"
            else:
                if cgpa < 6.0 or backlogs > 1:
                    status = "At Risk"

            student_tuples.append({
                "email": f"student{j}@platform.edu",
                "name": name,
                "dept_id": dept_ids[dept_code],
                "gender": gender,
                "batch": batch,
                "phone": f"98765{j:05d}",
                "cgpa": cgpa,
                "attendance": attendance,
                "backlogs": backlogs,
                "sgpa_sem1": round(max(4.0, min(10.0, cgpa + random.uniform(-0.5, 0.5))), 2),
                "sgpa_sem2": round(max(4.0, min(10.0, cgpa + random.uniform(-0.5, 0.5))), 2),
                "sgpa_sem3": round(max(4.0, min(10.0, cgpa + random.uniform(-0.5, 0.5))), 2),
                "sgpa_sem4": round(max(4.0, min(10.0, cgpa + random.uniform(-0.5, 0.5))), 2),
                "sgpa_sem5": round(max(4.0, min(10.0, cgpa + random.uniform(-0.5, 0.5))), 2),
                "sgpa_sem6": round(max(4.0, min(10.0, cgpa + random.uniform(-0.5, 0.5))), 2),
                "sgpa_sem7": round(max(4.0, min(10.0, cgpa + random.uniform(-0.5, 0.5))), 2) if batch == "2025" else None,
                "sgpa_sem8": round(max(4.0, min(10.0, cgpa + random.uniform(-0.5, 0.5))), 2) if batch == "2025" else None,
                "skills": json.dumps(selected_skills),
                "projects": json.dumps(projects),
                "internships": json.dumps([]),
                "certifications": json.dumps(certs),
                "github_url": f"https://github.com/student{j}",
                "linkedin_url": f"https://linkedin.com/in/student{j}",
                "leetcode_score": leetcode,
                "codechef_score": codechef,
                "hackerrank_score": hackerrank,
                "status": status,
                "profile_completed": True,
                "resume_text": f"RESUME OF {name}. Objective: High performing engineering student specializing in {dept_code}. Skills: {', '.join(selected_skills)}. Education: B.Tech, CGPA {cgpa}. Projects: {projects[0]['title'] if projects else 'Software Dashboard'}. Links: github.com/student{j}, linkedin.com/in/student{j}.",
                "resume_ats_score": random.randint(60, 95),
                "resume_analysis_json": json.dumps({
                    "ats_score": random.randint(60, 95),
                    "matching_skills": [s.upper() for s in selected_skills[:3]],
                    "missing_skills": ["AWS", "DOCKER", "KUBERNETES"],
                    "weak_sections": ["Format heading style could be improved", "No explicit internships registered"],
                    "grammar_issues": ["Verify Technical language capitalization rules."],
                    "project_suggestions": ["Implement microservices containers and build API clusters."],
                    "improvement_tips": ["Add hyperlinks to GitHub repositories.", "List detailed tech stacks under academic headings."]
                })
            })

        print("Executing bulk user inserts...")
        # Write users in chunks of 500
        for chunk_idx in range(0, len(student_tuples), 500):
            chunk = student_tuples[chunk_idx:chunk_idx+500]
            db.execute(
                User.__table__.insert(),
                [{"email": item["email"], "password_hash": shared_password_hash, "name": item["name"], "role": "student"} for item in chunk]
            )
        db.commit()

        # Fetch inserted user IDs by email to map students
        users_map = {u.email: u.id for u in db.query(User).filter(User.role == "student").all()}

        print("Executing bulk student profile inserts...")
        for chunk_idx in range(0, len(student_tuples), 500):
            chunk = student_tuples[chunk_idx:chunk_idx+500]
            student_mappings = []
            for item in chunk:
                uid = users_map[item["email"]]
                student_mappings.append({
                    "id": uid,
                    "dept_id": item["dept_id"],
                    "gender": item["gender"],
                    "batch": item["batch"],
                    "phone": item["phone"],
                    "cgpa": item["cgpa"],
                    "attendance": item["attendance"],
                    "backlogs": item["backlogs"],
                    "sgpa_sem1": item["sgpa_sem1"],
                    "sgpa_sem2": item["sgpa_sem2"],
                    "sgpa_sem3": item["sgpa_sem3"],
                    "sgpa_sem4": item["sgpa_sem4"],
                    "sgpa_sem5": item["sgpa_sem5"],
                    "sgpa_sem6": item["sgpa_sem6"],
                    "sgpa_sem7": item["sgpa_sem7"],
                    "sgpa_sem8": item["sgpa_sem8"],
                    "skills": item["skills"],
                    "projects": item["projects"],
                    "internships": item["internships"],
                    "certifications": item["certifications"],
                    "github_url": item["github_url"],
                    "linkedin_url": item["linkedin_url"],
                    "leetcode_score": item["leetcode_score"],
                    "codechef_score": item["codechef_score"],
                    "hackerrank_score": item["hackerrank_score"],
                    "status": item["status"],
                    "profile_completed": item["profile_completed"],
                    "resume_text": item["resume_text"],
                    "resume_ats_score": item["resume_ats_score"],
                    "resume_analysis_json": item["resume_analysis_json"]
                })
            db.execute(Student.__table__.insert(), student_mappings)
        db.commit()

        print("Generating Placement Drives...")
        # 10 completed, 5 active, 5 upcoming drives
        roles_pool = [
            ("Software Engineer", 12.0, "Hyderabad", ["CSE", "IT", "ECE"], 7.5),
            ("Data Analyst", 6.5, "Bengaluru", ["CSE", "IT", "ECE", "EEE"], 6.5),
            ("Embedded Engineer", 8.0, "Pune", ["ECE", "EEE"], 7.0),
            ("Graduate Engineer Trainee", 5.0, "Chennai", ["CSE", "IT", "ECE", "EEE", "MECH", "CIVIL"], 6.0),
            ("Associate Software Engineer", 4.5, "Hyderabad", ["CSE", "IT", "ECE"], 6.0),
            ("Cloud Associate", 7.0, "Bengaluru", ["CSE", "IT", "ECE"], 7.0),
            ("Construction Engineer", 5.5, "Mumbai", ["CIVIL"], 6.5),
            ("Automotive Design Engineer", 6.0, "Chennai", ["MECH"], 7.0)
        ]

        drives = []
        today = date.today()

        # Add 25 drives
        for i in range(1, 26):
            comp = companies[i % len(companies)]
            role_data = random.choice(roles_pool)
            
            # Drive timing
            if i <= 12:
                status = "Completed"
                interview_d = today - timedelta(days=random.randint(15, 60))
                deadline_d = interview_d - timedelta(days=7)
            elif i <= 20:
                status = "Active"
                interview_d = today + timedelta(days=random.randint(2, 10))
                deadline_d = interview_d - timedelta(days=5)
            else:
                status = "Upcoming"
                interview_d = today + timedelta(days=random.randint(15, 30))
                deadline_d = interview_d - timedelta(days=7)

            # Map skills to roles
            role_title = role_data[0]
            role_title_l = role_title.lower()
            if "frontend" in role_title_l or "react" in role_title_l:
                req_s = "React,JavaScript,TypeScript,CSS,HTML,Git"
            elif "backend" in role_title_l or "fastapi" in role_title_l:
                req_s = "Python,SQL,FastAPI,PostgreSQL,Docker,REST API"
            elif "data scientist" in role_title_l or "data analyst" in role_title_l:
                req_s = "Python,Pandas,SQL,Scikit-Learn,Machine Learning"
            elif "embedded" in role_title_l:
                req_s = "C,C++,Microcontrollers,RTOS,Assembly"
            else:
                req_s = "Java,SQL,Data Structures,Python,Algorithms"
                
            drive = PlacementDrive(
                company_id=comp.id,
                role=role_title,
                package_lpa=role_data[1] + round(random.uniform(-1.0, 3.0), 1),
                location=role_data[2],
                cgpa_cutoff=role_data[4],
                allowed_depts=",".join(role_data[3]),
                allowed_backlogs=0 if random.random() > 0.2 else 1,
                bond_details="No Bond" if random.random() > 0.5 else "2 Years",
                selection_process="Aptitude -> Technical Round -> HR Interview",
                interview_date=interview_d,
                deadline=deadline_d,
                status=status,
                
                # JD detail fields
                job_id=f"JD-2026-{i:03d}",
                responsibilities=f"Develop secure application architectures, integrate databases, write complex queries, and resolve production bugs. Team collaboration is required.",
                required_skills=req_s,
                preferred_skills="AWS,Docker,Kubernetes,CI/CD,Redis",
                job_type="Full-Time" if i % 4 != 0 else "Internship",
                work_mode="Onsite" if i % 3 == 0 else ("Hybrid" if i % 3 == 1 else "Remote"),
                openings_count=random.randint(3, 12),
                hiring_process="Online Assessment MCQ -> Technical Interviews (2 Rounds) -> HR Panel Discussion",
                jd_pdf_path=f"uploads/jd/JD-2026-{i:03d}.pdf",
                company_logo=f"https://logo.clearbit.com/{comp.name.lower().replace(' ', '')}.com"
            )
            db.add(drive)
        db.commit()

        # Retrieve drives
        drives = db.query(PlacementDrive).all()
        # Fetch current batch students (2026)
        active_students = db.query(Student).filter(Student.batch == "2026").all()
        # Past batch students (2025)
        past_students = db.query(Student).filter(Student.batch == "2025").all()

        print("Generating Student Applications...")
        # For Completed drives, register applications and push rounds to Selected/Rejected
        # For Active drives, register applications in various rounds
        # Let's seed around 1500 applications to reflect real activity
        applications = []
        
        # Completed Drives Application Seeding (drives 0 to 11)
        completed_drives = [d for d in drives if d.status == "Completed"]
        active_drives = [d for d in drives if d.status == "Active"]

        print(f"Generating outcomes for {len(completed_drives)} completed drives...")
        for drive in completed_drives:
            allowed_dept_list = drive.allowed_depts.split(",")
            eligible_pool = [s for s in active_students + past_students if s.department.code in allowed_dept_list and s.cgpa >= drive.cgpa_cutoff and s.backlogs <= drive.allowed_backlogs]
            
            # Subsample applicants (e.g. 50-80 students apply per drive)
            num_applicants = min(len(eligible_pool), random.randint(50, 80))
            applicants = random.sample(eligible_pool, num_applicants)

            for student in applicants:
                # Randomize final status: Selected (12% chance), Rejected (88%)
                outcome = "Selected" if random.random() < 0.15 else "Rejected"
                
                # Joining status
                j_status = "Pending"
                if outcome == "Selected":
                    j_status = "Accepted" if random.random() > 0.2 else "Declined"
                    student.status = "Placed"  # Mark student as Placed

                app = Application(
                    student_id=student.id,
                    drive_id=drive.id,
                    status=outcome,
                    current_round="Selected" if outcome == "Selected" else random.choice(["Coding", "Technical", "HR"]),
                    joining_status=j_status,
                    remarks="Process completed successfully." if outcome == "Selected" else "Could not clear interview round.",
                    applied_date=datetime.combine(drive.deadline - timedelta(days=2), datetime.min.time())
                )
                db.add(app)
        db.commit()

        # Active Drives Applications Seeding
        print(f"Generating applications for {len(active_drives)} active drives...")
        for drive in active_drives:
            allowed_dept_list = drive.allowed_depts.split(",")
            # Current batch students apply to active drives
            eligible_pool = [s for s in active_students if s.department.code in allowed_dept_list and s.cgpa >= drive.cgpa_cutoff and s.backlogs <= drive.allowed_backlogs]
            
            num_applicants = min(len(eligible_pool), random.randint(40, 70))
            applicants = random.sample(eligible_pool, num_applicants)

            for student in applicants:
                # Active applications can be in different rounds: Applied, Shortlisted, Round 1, Round 2, HR, Selected, Rejected
                status_choices = ["Applied", "Shortlisted", "Round 1", "Round 2", "Technical", "HR"]
                curr_status = random.choice(status_choices)
                
                app = Application(
                    student_id=student.id,
                    drive_id=drive.id,
                    status="Eligible" if curr_status == "Applied" else curr_status,
                    current_round=curr_status,
                    joining_status="Pending",
                    applied_date=datetime.combine(drive.deadline - timedelta(days=1), datetime.min.time())
                )
                db.add(app)
        db.commit()

        # Generate Interview Records & NLP Feedback for Selected/Rejected students
        print("Generating Interview records & NLP Feedback...")
        apps_with_interviews = db.query(Application).filter(Application.status.in_(["Selected", "Rejected", "HR", "Technical"])).limit(300).all()
        
        feedback_texts = [
            ("The interview was very smooth. The panel was friendly and supportive. They asked core questions on OOPs concepts like polymorphism and inheritance in Java. Also asked one SQL query about finding the second highest salary using a subquery.", 4, "OOPs, Java, SQL, Joins"),
            ("A very tough technical interview. The interviewer was cold and rushed through the resume. They gave a dynamic programming problem on Knapsack which I struggled to solve. Also asked about Operating Systems, specifically deadlock conditions.", 2, "Dynamic Programming, OS, Deadlock, Knapsack"),
            ("The coding round was moderately difficult. Question was related to reversing a linked list. Then the HR round was encouraging. They focused on communication skills and project descriptions.", 4, "Linked List, HR, Communication"),
            ("They asked a lot of questions about cloud scaling and AWS EC2 instances. The system design round got complicated. Felt stressful but managed to answer. Rejection reason was likely lack of detail in systems.", 3, "AWS, Cloud, System Design"),
            ("Super easy interview. Asked simple Python list operations, git basic commands, and database normalization forms. The interview panel was nice and polite.", 5, "Python, Git, DBMS, Normalization"),
            ("I was nervous but they made me comfortable. The primary focus was on React hooks, Javascript promises, and REST API creation. Extracted feedback suggests high interest in frontend.", 4, "React, Javascript, REST API, Frontend"),
            ("Tough round on networking protocols. Asked to explain TCP/IP vs UDP and DNS resolution. Got stuck in networking concepts. Need to prepare computer networks.", 2, "Computer Networks, TCP, UDP, DNS"),
            ("Mainly discussed my final year project. They asked about SQL indexes and why index improves query speed. Very positive experience.", 4, "Projects, SQL, Indexes, DBMS"),
            ("The interviewer asked me to write code on a whiteboard for Binary Search Tree traversal. I got confused in recursion base case. They rejected me due to slow coding speed.", 2, "Binary Search Tree, Recursion, DSA"),
            ("Great HR round. They asked about relocation plans, bond details, and situational questions. Prepared for 2 days. Clear instructions.", 5, "HR, Situation, Relocation")
        ]

        for idx, app in enumerate(apps_with_interviews):
            round_name = random.choice(["Coding", "Technical", "HR"])
            int_status = "Passed" if app.status == "Selected" else ("Failed" if app.status == "Rejected" else "Scheduled")
            
            interview = Interview(
                application_id=app.id,
                student_id=app.student_id,
                round_name=round_name,
                status=int_status,
                interview_date=app.applied_date + timedelta(days=10),
                remarks="Performance evaluated."
            )
            db.add(interview)
            db.commit() # Commit to get interview.id

            # Add feedback
            fb_choice = feedback_texts[idx % len(feedback_texts)]
            text, diff, kws = fb_choice
            
            sentiment = nlp_analyzer.analyze_sentiment(text)
            topic = nlp_analyzer.identify_topic(text)

            feedback = Feedback(
                interview_id=interview.id,
                experience_text=text,
                questions_asked=kws,
                difficulty_rating=diff,
                preparation_time=random.choice(["1 week", "3 days", "2 weeks", "None"]),
                suggestions="Review core subjects before attending.",
                sentiment_score=sentiment,
                extracted_keywords=kws,
                topic_analysis=topic
            )
            db.add(feedback)
        db.commit()

        # Update ALL Students with AI predictions!
        print("Calculating AI readiness & probability scores for all 3,000 students...")
        all_students = db.query(Student).all()
        
        # Fit predictor model dynamically based on this generated data
        print("Training Random Forest predictor on seed data...")
        predictor.train_model(db)
        
        # Batch updates for student readiness/probability
        for index, student in enumerate(all_students):
            report = predictor.evaluate_student(student, db)
            student.readiness_score = report["readiness_score"]
            student.placement_probability = report["placement_probability"]
            student.ai_recommendations = json.dumps({
                "skills_gap": report["skills_gap"],
                "recommended_skills": report["recommended_skills"],
                "recommended_projects": report["recommended_projects"],
                "recommended_certifications": report["recommended_certifications"],
                "improvement_tips": report["improvement_tips"]
            })
            
            # Recalculate status for active students based on risk detection
            if student.batch == "2026" and student.status != "Placed":
                if report["at_risk"]:
                    student.status = "At Risk"
                else:
                    student.status = "Unplaced"
                    
            if index % 500 == 0 and index > 0:
                print(f"Processed {index} student profiles...")
        
        db.commit()

        print("Creating system logs & notification reports...")
        # Sample system logs
        logs = [
            SystemLog(user_email="admin@platform.edu", action="System Seeding", details="Initial database seeding with 3000 students, 155 companies, and 25 drives."),
            SystemLog(user_email="admin@platform.edu", action="Model Training", details="Random Forest Classifier trained successfully on student placement records."),
            SystemLog(user_email="faculty.cse@platform.edu", action="View Analytics", details="Accessed CSE placement metrics and AI reports dashboard.")
        ]
        db.add_all(logs)

        # Sample notifications
        for s in active_students[:15]:
            db.add(Notification(
                user_id=s.id,
                title="New Placement Drive Active",
                message="Google is hiring Software Engineers. Apply before the deadline."
            ))
        db.commit()

        print("Database Seeding Completed successfully!")

    except Exception as e:
        print(f"Seeding failed: {e}")
        db.rollback()
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
