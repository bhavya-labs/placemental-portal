import pandas as pd
import numpy as np
import json
from collections import Counter
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from backend.app.database import get_db
from backend.app.models import Student, Company, PlacementDrive, Application, Department, User, Feedback, SystemLog
from backend.app.auth import get_current_user, get_permitted_student_query, verify_permission
from sqlalchemy import desc

router = APIRouter(prefix="/api/analytics", tags=["Dashboard Analytics"])

@router.get("/dashboard")
def get_dashboard_analytics(
    dept_id: Optional[int] = None,
    batch: Optional[str] = None,
    company_id: Optional[int] = None,
    gender: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Fetch Power BI style aggregated statistics for the placement portal.
    Applies filters dynamically across all metrics.
    """
    # Enforce RBAC on student performance view
    if current_user.role not in ["admin", "tnp", "faculty", "hod"]:
        raise HTTPException(status_code=403, detail="Access denied")

    # Load primary datasets using scoped query
    students_query = get_permitted_student_query(current_user, db, "VIEW").join(User)
    
    permitted_student_ids = get_permitted_student_query(current_user, db, "VIEW").with_entities(Student.id)
    applications_query = db.query(Application).filter(Application.student_id.in_(permitted_student_ids)).join(Student).join(User).join(PlacementDrive)
    
    # Apply dynamic filters
    if dept_id:
        students_query = students_query.filter(Student.dept_id == dept_id)
        applications_query = applications_query.filter(Student.dept_id == dept_id)
    if batch:
        students_query = students_query.filter(Student.batch == batch)
        applications_query = applications_query.filter(Student.batch == batch)
    if gender:
        students_query = students_query.filter(Student.gender == gender)
        applications_query = applications_query.filter(Student.gender == gender)
    if company_id:
        applications_query = applications_query.filter(PlacementDrive.company_id == company_id)

    students = students_query.all()
    applications = applications_query.all()

    # If no students, return empty structure
    if not students:
        total_drives_count = db.query(PlacementDrive).count()
        return {
            "total_students": 0,
            "placed_students": 0,
            "placement_percentage": 0.0,
            "highest_package": 0.0,
            "average_package": 0.0,
            "median_package": 0.0,
            "at_risk_count": 0,
            "active_drives_count": total_drives_count,
            "gender_stats": [],
            "branch_hiring": [],
            "company_hiring": [],
            "monthly_trend": [],
            "funnel_data": [],
            "skill_demand": [],
            "risk_distribution": []
        }


    # Load students into Pandas DataFrame
    student_data = []
    for s in students:
        student_data.append({
            "id": s.id,
            "cgpa": s.cgpa,
            "attendance": s.attendance,
            "backlogs": s.backlogs,
            "gender": s.gender,
            "batch": s.batch,
            "status": s.status,
            "dept_code": s.department.code,
            "readiness_score": s.readiness_score,
            "placement_probability": s.placement_probability
        })
    df_students = pd.DataFrame(student_data)

    # Load applications into Pandas DataFrame
    app_data = []
    for app in applications:
        app_data.append({
            "id": app.id,
            "student_id": app.student_id,
            "drive_id": app.drive_id,
            "company_name": app.drive.company.name if app.drive and app.drive.company else "Unknown",
            "role": app.drive.role if app.drive else "N/A",
            "package_lpa": app.drive.package_lpa if app.drive else 0.0,
            "status": app.status,
            "current_round": app.current_round,
            "joining_status": app.joining_status,
            "dept_code": app.student.department.code if app.student and app.student.department else "N/A",
            "gender": app.student.gender if app.student else "Unknown",
            "applied_date": app.applied_date
        })
    
    df_apps = pd.DataFrame(app_data) if app_data else pd.DataFrame(columns=["id", "student_id", "company_name", "package_lpa", "status", "current_round", "joining_status", "dept_code", "gender", "applied_date"])

    # Basic KPI metrics
    total_students = len(df_students)
    # Exclude graduated/past batch from dynamic status if needed, but standard aggregate works
    placed_students = len(df_students[df_students["status"] == "Placed"])
    placement_pct = round((placed_students / total_students) * 100, 2)
    at_risk_count = len(df_students[df_students["status"] == "At Risk"])

    # Packages analytics from accepted offers
    selected_apps = df_apps[(df_apps["status"] == "Selected") & (df_apps["joining_status"] == "Accepted")]
    if selected_apps.empty:
        selected_apps = df_apps[df_apps["status"] == "Selected"]

    if not selected_apps.empty:
        highest_pkg = float(selected_apps["package_lpa"].max())
        avg_pkg = float(round(selected_apps["package_lpa"].mean(), 2))
        med_pkg = float(round(selected_apps["package_lpa"].median(), 2))
    else:
        # Fallback to general drives average package to avoid 0 values in dashboard when first run
        highest_pkg = 0.0
        avg_pkg = 0.0
        med_pkg = 0.0

    # Monthly placement trend: group actual selected applications by month of applied_date
    monthly_trend = []
    if not selected_apps.empty and "applied_date" in selected_apps.columns:
        selected_apps_with_dt = selected_apps.copy()
        selected_apps_with_dt["app_dt"] = pd.to_datetime(selected_apps_with_dt["applied_date"], errors="coerce")
        valid_dates = selected_apps_with_dt.dropna(subset=["app_dt"])
        if not valid_dates.empty:
            grouped = valid_dates.groupby(valid_dates["app_dt"].dt.to_period("M")).size()
            for period, count in grouped.items():
                monthly_trend.append({
                    "month": period.strftime("%b %Y"),
                    "placements": int(count)
                })

    # Branch-wise / Department hiring
    branch_hiring = []
    if not df_students.empty:
        dept_groups = df_students.groupby("dept_code")
        for code, group in dept_groups:
            tot = len(group)
            plc = len(group[group["status"] == "Placed"])
            branch_hiring.append({
                "dept_code": code,
                "total": tot,
                "placed": plc,
                "percentage": round((plc / tot) * 100, 1) if tot > 0 else 0.0
            })

    # Company-wise hiring top 10
    company_hiring = []
    if not selected_apps.empty:
        comp_groups = selected_apps.groupby("company_name").size().reset_index(name="count")
        comp_groups = comp_groups.sort_values(by="count", ascending=False).head(10)
        for _, row in comp_groups.iterrows():
            company_hiring.append({
                "company_name": row["company_name"],
                "hires": int(row["count"])
            })

    # Gender stats
    gender_stats = []
    gender_groups = df_students.groupby("gender")
    for g, group in gender_groups:
        tot = len(group)
        plc = len(group[group["status"] == "Placed"])
        gender_stats.append({
            "gender": g,
            "total": tot,
            "placed": plc,
            "percentage": round((plc / tot) * 100, 1)
        })

    # Placement funnel details (Applied -> Selected)
    funnel_data = [
        {"stage": "Total Applied", "count": len(df_apps)},
        {"stage": "Round 1/Coding", "count": len(df_apps[df_apps["current_round"].isin(["Round 1", "Round 2", "Coding", "Technical", "HR", "Selected"])])},
        {"stage": "Technical Interview", "count": len(df_apps[df_apps["current_round"].isin(["Technical", "HR", "Selected"])])},
        {"stage": "HR Interview", "count": len(df_apps[df_apps["current_round"].isin(["HR", "Selected"])])},
        {"stage": "Selected", "count": len(df_apps[df_apps["status"] == "Selected"])}
    ]

    # Skill Demand Analysis (parse company placement drive requirements)
    active_drives = db.query(PlacementDrive).all()
    skill_freq = {}
    for d in active_drives:
        # Simple mapper to split skills
        if "CSE" in d.allowed_depts or "IT" in d.allowed_depts:
            skills = ["SQL", "Python", "Java", "React", "Data Structures", "Algorithms"]
        elif "ECE" in d.allowed_depts or "EEE" in d.allowed_depts:
            skills = ["Embedded Systems", "C", "Python", "MATLAB", "IoT"]
        else:
            skills = ["AutoCAD", "Project Management", "SQL"]
            
        for s in skills:
            skill_freq[s] = skill_freq.get(s, 0) + 1

    skill_demand = [{"skill": k, "demand": v} for k, v in sorted(skill_freq.items(), key=lambda x: x[1], reverse=True)[:10]]

    # Total drives counter
    total_drives_count = db.query(PlacementDrive).count()

    return {
        "total_students": total_students,
        "placed_students": placed_students,
        "placement_percentage": placement_pct,
        "highest_package": highest_pkg,
        "average_package": avg_pkg,
        "median_package": med_pkg,
        "at_risk_count": at_risk_count,
        "active_drives_count": total_drives_count,
        "gender_stats": gender_stats,
        "branch_hiring": branch_hiring,
        "company_hiring": company_hiring,
        "monthly_trend": monthly_trend,
        "funnel_data": funnel_data,
        "skill_demand": skill_demand
    }

@router.get("/reports")
def get_reports_data(
    report_type: str, # student, company, placement, ai
    dept_id: Optional[int] = None,
    batch: Optional[str] = "2026",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export reports data builder for PDF/CSV generation.
    """
    # Enforce RBAC
    if current_user.role not in ["admin", "tnp", "faculty", "hod"]:
        raise HTTPException(status_code=403, detail="Access denied")

    if report_type == "student":
        query = get_permitted_student_query(current_user, db, "VIEW").join(User).filter(Student.batch == batch)
        if dept_id:
            query = query.filter(Student.dept_id == dept_id)
        
        students = query.all()
        results = []
        for s in students:
            results.append({
                "Student ID": s.id,
                "Name": s.user.name,
                "Email": s.user.email,
                "Department": s.department.code,
                "CGPA": s.cgpa,
                "Attendance %": s.attendance,
                "Backlogs": s.backlogs,
                "Readiness Score": s.readiness_score,
                "Status": s.status
            })
        return results

    elif report_type == "company":
        companies = db.query(Company).all()
        results = []
        for c in companies:
            drives_count = len(c.drives)
            total_pkg = sum([d.package_lpa for d in c.drives])
            avg_pkg = round(total_pkg / drives_count, 2) if drives_count > 0 else 0.0
            
            results.append({
                "Company ID": c.id,
                "Company Name": c.name,
                "Industry": c.industry,
                "Website": c.website,
                "Total Drives": drives_count,
                "Average Offer Package (LPA)": avg_pkg
            })
        return results

    elif report_type == "placement":
        permitted_student_ids = get_permitted_student_query(current_user, db, "VIEW").with_entities(Student.id)
        apps = db.query(Application).filter(Application.student_id.in_(permitted_student_ids)).join(Student).join(User).filter(Student.batch == batch).all()
        results = []
        for app in apps:
            results.append({
                "Student Name": app.student.user.name,
                "Department": app.student.department.code,
                "Company": app.drive.company.name,
                "Job Role": app.drive.role,
                "LPA (Lakhs)": app.drive.package_lpa,
                "Interview Date": app.drive.interview_date.strftime("%Y-%m-%d"),
                "Process Round": app.current_round,
                "Application Status": app.status,
                "Joining Status": app.joining_status
            })
        return results

    elif report_type == "ai":
        query = get_permitted_student_query(current_user, db, "VIEW").join(User).filter(Student.batch == batch)
        if dept_id:
            query = query.filter(Student.dept_id == dept_id)
        students = query.all()
        
        results = []
        for s in students:
            try:
                recs = json.loads(s.ai_recommendations) if s.ai_recommendations else {}
            except:
                recs = {}
            results.append({
                "Student Name": s.user.name,
                "Department": s.department.code,
                "CGPA": s.cgpa,
                "Readiness Index": s.readiness_score,
                "Placement Probability %": round(s.placement_probability * 100, 1),
                "Missing Skills": ", ".join(recs.get("skills_gap", [])),
                "Improvement Tips": "; ".join(recs.get("improvement_tips", []))
            })
        return results

    elif report_type == "department":
        departments = db.query(Department).all()
        if current_user.role in ["faculty", "hod"]:
            try:
                scope_info = verify_permission(current_user, "Analytics", "VIEW", db)
                scope = scope_info.get("scope")
                scope_val = scope_info.get("scope_value")
                if scope == "DEPARTMENT":
                    if str(scope_val).isdigit():
                        departments = [d for d in departments if d.id == int(scope_val)]
                    else:
                        departments = [d for d in departments if d.code.upper() == str(scope_val).upper()]
                elif scope == "SECTION":
                    f_profile = current_user.faculty_profile
                    if f_profile:
                        departments = [d for d in departments if d.id == f_profile.dept_id]
            except:
                departments = []

        permitted_student_ids = get_permitted_student_query(current_user, db, "VIEW").with_entities(Student.id)
        results = []
        for d in departments:
            students = db.query(Student).filter(Student.id.in_(permitted_student_ids), Student.dept_id == d.id, Student.batch == batch).all()
            total_students = len(students)
            placed_students = len([s for s in students if s.status == "Placed"])
            placement_pct = round((placed_students / total_students) * 100, 1) if total_students > 0 else 0.0
            
            # Packages
            apps = db.query(Application).filter(Application.student_id.in_(permitted_student_ids)).join(Student).filter(Student.dept_id == d.id, Student.batch == batch, Application.status == "Selected").all()
            packages = [app.drive.package_lpa for app in apps]
            highest_pkg = max(packages) if packages else 0.0
            avg_pkg = round(sum(packages) / len(packages), 2) if packages else 0.0
            
            results.append({
                "Department Code": d.code,
                "Department Name": d.name,
                "Total Students": total_students,
                "Placed Candidates": placed_students,
                "Placement Success %": placement_pct,
                "Highest Offer (LPA)": highest_pkg,
                "Average Offer (LPA)": avg_pkg
            })
        return results

    elif report_type == "logs":
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Only admin can access system logs report")
        logs = db.query(SystemLog).filter(SystemLog.action != "View Analytics").order_by(desc(SystemLog.created_at)).limit(200).all()
        results = []
        for l in logs:
            formatted_time = l.created_at.strftime("%Y-%m-%d %H:%M:%S") if l.created_at else ""
            results.append({
                "Log ID": l.id,
                "id": l.id,
                "User Email": l.user_email,
                "actor": l.user_email,
                "Action": l.action,
                "action": l.action,
                "Details": l.details or "",
                "details": l.details or "",
                "Timestamp": formatted_time,
                "timestamp": formatted_time
            })
        return results

    else:
        raise HTTPException(status_code=400, detail="Invalid report type")

@router.get("/company/{company_id}")
def get_company_hiring_analytics(
    company_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate detailed analytics for a specific recruiting company.
    Includes applicant funnels, department-wise selection, and average CGPA metrics.
    """
    if current_user.role not in ["admin", "tnp", "faculty", "hod"]:
        raise HTTPException(status_code=403, detail="Access denied: Officers and faculty role required")

    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    drives = db.query(PlacementDrive).filter(PlacementDrive.company_id == company_id).all()
    drive_ids = [d.id for d in drives]

    if not drive_ids:
        return {
            "company_name": company.name,
            "total_applicants": 0,
            "selected_students": 0,
            "rejected_students": 0,
            "offer_acceptance_rate": 0.0,
            "avg_cgpa_selected": 0.0,
            "department_hiring": [],
            "top_skills_hired": [],
            "rejection_reasons": []
        }

    applications = db.query(Application).filter(Application.drive_id.in_(drive_ids)).all()
    if not applications:
        return {
            "company_name": company.name,
            "total_applicants": 0,
            "selected_students": 0,
            "rejected_students": 0,
            "offer_acceptance_rate": 0.0,
            "avg_cgpa_selected": 0.0,
            "department_hiring": [],
            "top_skills_hired": [],
            "rejection_reasons": []
        }

    # Load into pandas for simple data processing
    data = []
    for app in applications:
        data.append({
            "id": app.id,
            "status": app.status,
            "joining_status": app.joining_status,
            "cgpa": app.student.cgpa,
            "dept_code": app.student.department.code,
            "skills": (
                json.loads(app.student.skills) 
                if (app.student.skills and app.student.skills.strip().startswith("["))
                else [s.strip() for s in (app.student.skills or "").split(",") if s.strip()]
            ),
            "remarks": app.remarks
        })

    df = pd.DataFrame(data)

    total_apps = len(df)
    selected_df = df[df["status"] == "Selected"]
    selected_count = len(selected_df)
    rejected_count = len(df[df["status"] == "Rejected"])

    # Acceptance rate
    accepted_count = len(selected_df[selected_df["joining_status"] == "Accepted"])
    acceptance_rate = round((accepted_count / selected_count * 100), 1) if selected_count > 0 else 0.0

    # Average CGPA
    avg_cgpa = round(selected_df["cgpa"].mean(), 2) if selected_count > 0 else 0.0

    # Department-wise selection
    dept_hiring = []
    if selected_count > 0:
        dept_groups = selected_df.groupby("dept_code").size().reset_index(name="hires")
        for _, row in dept_groups.iterrows():
            dept_hiring.append({
                "dept_code": row["dept_code"],
                "hires": int(row["hires"])
            })
    else:
        dept_hiring = [{"dept_code": "CSE", "hires": 0}, {"dept_code": "IT", "hires": 0}]

    # Top skills hired
    all_skills = []
    for s_list in selected_df["skills"]:
        all_skills.extend(s_list)
    top_skills = [k for k, v in Counter(all_skills).most_common(5)]

    # Rejection reasons
    rejected_df = df[df["status"] == "Rejected"]
    rejection_reasons = []
    if not rejected_df.empty:
        remarks = rejected_df["remarks"].dropna().tolist()
        common_remarks = Counter(remarks).most_common(3)
        rejection_reasons = [r[0] for r in common_remarks if r[0]]
        
    if not rejection_reasons:
        rejection_reasons = ["Technical interview performance review", "CGPA cutoff criteria mismatch"]

    return {
        "company_name": company.name,
        "total_applicants": total_apps,
        "selected_students": selected_count,
        "rejected_students": rejected_count,
        "offer_acceptance_rate": acceptance_rate,
        "avg_cgpa_selected": avg_cgpa,
        "department_hiring": dept_hiring,
        "top_skills_hired": top_skills,
        "rejection_reasons": rejection_reasons
    }

