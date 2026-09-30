from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, date
from typing import List, Optional
import json
from backend.app.database import get_db
from backend.app.models import User, Student, PlacementDrive, Application, Interview, Feedback, Notification, SystemLog
from backend.app.schemas import ApplicationCreate, ApplicationStatusUpdate, InterviewCreate, FeedbackCreate
from backend.app.auth import get_current_user, get_current_student, verify_permission, enforce_student_scope
from backend.app.ml.nlp_feedback import nlp_analyzer

router = APIRouter(prefix="", tags=["Applications & Interviews"])

# APPLICATIONS

@router.post("/api/applications")
def apply_to_drive(
    app_data: ApplicationCreate,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    drive = db.query(PlacementDrive).filter(PlacementDrive.id == app_data.drive_id).first()
    if not drive:
        raise HTTPException(status_code=404, detail="Placement drive not found")
        
    # Check deadline
    if date.today() > drive.deadline:
        raise HTTPException(status_code=400, detail="Application deadline has passed")
        
    # Check if already applied
    existing = db.query(Application).filter(
        Application.student_id == current_student.id,
        Application.drive_id == app_data.drive_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="You have already applied for this drive")

    # Eligibility validation
    allowed_depts = [d.strip().upper() for d in drive.allowed_depts.split(",")]
    dept_code = current_student.department.code.upper()
    
    if "ALL" not in allowed_depts and dept_code not in allowed_depts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Department {dept_code} is not eligible for this drive"
        )
        
    if current_student.cgpa < drive.cgpa_cutoff:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Your CGPA ({current_student.cgpa}) is below the required cutoff ({drive.cgpa_cutoff})"
        )
        
    if current_student.backlogs > drive.allowed_backlogs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Your backlogs ({current_student.backlogs}) exceed the allowed limit ({drive.allowed_backlogs})"
        )

    if drive.batch and current_student.batch != drive.batch:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Your graduation batch ({current_student.batch}) does not match the drive criteria ({drive.batch})"
        )

    if drive.min_attendance and current_student.attendance < drive.min_attendance:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Your academic attendance ({current_student.attendance}%) is below the required minimum ({drive.min_attendance}%)"
        )

    # Create application
    application = Application(
        student_id=current_student.id,
        drive_id=drive.id,
        status="Applied",
        current_round="Applied",
        joining_status="Pending"
    )
    db.add(application)
    db.commit()
    db.refresh(application)

    # System Log
    log = SystemLog(
        user_email=current_student.user.email,
        action="Apply Drive",
        details=f"Applied for drive ID {drive.id} ({drive.company.name} - {drive.role})"
    )
    db.add(log)
    db.commit()

    return {"message": "Application submitted successfully!", "application_id": application.id}

@router.delete("/api/applications/{application_id}")
def withdraw_application(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application record not found")
        
    if current_user.role == "student":
        student_profile = current_user.student_profile
        if not student_profile or app.student_id != student_profile.id:
            raise HTTPException(status_code=403, detail="Access denied: You can only withdraw your own applications")
            
        drive = app.drive
        if drive and drive.deadline and date.today() > drive.deadline:
            raise HTTPException(status_code=400, detail="Cannot withdraw application after drive application deadline has passed")
            
        if app.status in ["Selected", "Placed", "Rejected"]:
            raise HTTPException(status_code=400, detail=f"Cannot withdraw application with status '{app.status}'")
    elif current_user.role not in ["admin", "tnp"]:
        raise HTTPException(status_code=403, detail="Access denied: Only applicant or administrator can withdraw applications")

    if app.status == "Withdrawn":
        raise HTTPException(status_code=400, detail="Application has already been withdrawn")

    drive = app.drive
    drive_info = f"Drive ID {app.drive_id} ({drive.company.name if drive and drive.company else ''} - {drive.role if drive else ''})"
    
    # Remove associated interviews and feedback if any
    db.query(Feedback).filter(Feedback.interview_id.in_(
        db.query(Interview.id).filter(Interview.application_id == application_id)
    )).delete(synchronize_session=False)
    db.query(Interview).filter(Interview.application_id == application_id).delete(synchronize_session=False)
    
    db.delete(app)
    db.commit()
    
    log = SystemLog(
        user_email=current_user.email,
        action="Withdraw Application",
        details=f"Withdrew application ID {application_id} for {drive_info}"
    )
    db.add(log)
    db.commit()
    
    return {"message": "Application successfully withdrawn"}

@router.get("/api/applications/student/{student_id}")
def get_student_applications(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    student = enforce_student_scope(current_user, student_id, db, "VIEW")

    applications = db.query(Application).filter(Application.student_id == student_id).all()
    results = []
    
    for app in applications:
        results.append({
            "id": app.id,
            "drive_id": app.drive_id,
            "company_name": app.drive.company.name,
            "role": app.drive.role,
            "package_lpa": app.drive.package_lpa,
            "status": app.status,
            "current_round": app.current_round,
            "joining_status": app.joining_status,
            "remarks": app.remarks,
            "applied_date": app.applied_date
        })
    return results

@router.put("/api/applications/{application_id}/status")
def update_application_status(
    application_id: int,
    status_data: ApplicationStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_permission(current_user, "Placement Drives", "EDIT", db)
        
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application record not found")

    app.status = status_data.status
    app.current_round = status_data.current_round
    
    if status_data.joining_status:
        app.joining_status = status_data.joining_status
        
    app.remarks = status_data.remarks
    db.commit()

    # If the student got selected and accepted the offer, mark student status as "Placed"
    student = app.student
    if app.status == "Selected" and app.joining_status == "Accepted":
        student.status = "Placed"
    elif app.status == "Rejected" and student.status != "Placed":
        # Recalculate if student falls back to risk category
        pass 
        
    db.commit()

    # Send Notification to Student
    notif = Notification(
        user_id=student.id,
        title=f"Application Update: {app.drive.company.name}",
        message=f"Your application status for {app.drive.role} has been updated to {app.status} ({app.current_round})."
    )
    db.add(notif)
    
    # Notify Parent on selection (Req 12)
    if app.status == "Selected":
        parent_notif = Notification(
            user_id=student.id,
            title="[Parent Alert] Selection Result",
            message=f"Congratulations! Your ward {student.user.name} has been selected by {app.drive.company.name} for the role of '{app.drive.role}'."
        )
        db.add(parent_notif)
    
    # Audit log
    log = SystemLog(
        user_email=current_user.email,
        action="Update Application Status",
        details=f"Updated Application ID {application_id} to status: {app.status}, round: {app.current_round}."
    )
    db.add(log)
    db.commit()

    return {"message": "Application status updated and student notified!"}

# INTERVIEWS & FEEDBACK

@router.post("/api/interviews")
def schedule_interview(
    interview_data: InterviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_permission(current_user, "Placement Drives", "EDIT", db)

    app = db.query(Application).filter(Application.id == interview_data.application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    interview = Interview(
        application_id=interview_data.application_id,
        student_id=app.student_id,
        round_name=interview_data.round_name,
        status="Scheduled",
        interview_date=interview_data.interview_date,
        remarks=interview_data.remarks
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)

    # Notify student
    notif = Notification(
        user_id=app.student_id,
        title="New Interview Scheduled",
        message=f"A new interview round '{interview.round_name}' is scheduled for {app.drive.company.name} on {interview.interview_date.strftime('%Y-%m-%d %H:%M')}."
    )
    db.add(notif)
    
    # Notify Parent on interview (Req 12)
    parent_notif = Notification(
        user_id=app.student_id,
        title="[Parent Alert] Interview Scheduled",
        message=f"Important: An interview round '{interview.round_name}' has been scheduled for your ward {app.student.user.name} by {app.drive.company.name} on {interview.interview_date.strftime('%Y-%m-%d %H:%M')}."
    )
    db.add(parent_notif)
    db.commit()

    return {"message": "Interview round scheduled successfully!", "interview_id": interview.id}

@router.get("/api/interviews/student/{student_id}")
def get_student_interviews(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    student = enforce_student_scope(current_user, student_id, db, "VIEW")

    interviews = db.query(Interview).filter(Interview.student_id == student_id).all()
    results = []
    
    for i in interviews:
        results.append({
            "id": i.id,
            "application_id": i.application_id,
            "company_name": i.application.drive.company.name,
            "role": i.application.drive.role,
            "round_name": i.round_name,
            "status": i.status,
            "interview_date": i.interview_date,
            "remarks": i.remarks,
            "has_feedback": db.query(Feedback).filter(Feedback.interview_id == i.id).count() > 0
        })
    return results

@router.post("/api/interviews/{interview_id}/feedback")
def submit_interview_feedback(
    interview_id: int,
    fb_data: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview record not found")

    # Verify student is submitter
    if current_user.role == "student" and interview.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Check duplicate
    existing = db.query(Feedback).filter(Feedback.interview_id == interview_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Feedback already submitted for this interview")

    # NLP Analysis
    nlp_results = nlp_analyzer.process_feedback(fb_data.experience_text)

    # Save feedback
    feedback = Feedback(
        interview_id=interview_id,
        experience_text=fb_data.experience_text,
        questions_asked=fb_data.questions_asked,
        difficulty_rating=fb_data.difficulty_rating,
        preparation_time=fb_data.preparation_time,
        suggestions=fb_data.suggestions,
        sentiment_score=nlp_results["sentiment_score"],
        extracted_keywords=nlp_results["extracted_keywords"],
        topic_analysis=nlp_results["topic_analysis"]
    )
    db.add(feedback)
    
    # Also update interview status to Completed/Passed/Failed based on suggestions or manual status
    interview.status = "Completed"
    
    db.commit()

    log = SystemLog(
        user_email=current_user.email,
        action="Submit Feedback",
        details=f"Submitted interview feedback for Interview ID {interview_id}. Topic: {nlp_results['topic_analysis']}, Sentiment: {nlp_results['sentiment_score']}"
    )
    db.add(log)
    db.commit()

    return {"message": "Feedback submitted and processed successfully!"}
