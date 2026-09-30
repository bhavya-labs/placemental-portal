import json
import re
from collections import Counter
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from backend.app.database import get_db
from backend.app.models import Student, Feedback, User, Interview, PlacementDrive, Department, Application
from backend.app.ml.predictor import predictor
from backend.app.ml.nlp_feedback import nlp_analyzer
from backend.app.ml.resume_scanner import resume_scanner
from backend.app.ml.feedback_miner import feedback_miner
from backend.app.auth import get_current_user, get_current_student, enforce_student_scope

router = APIRouter(prefix="/api/ai", tags=["AI Analytics & Feedback Mining"])

@router.get("/model-metrics")
def get_model_evaluation_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get evaluation metrics from the 80/20 train/test split of the Random Forest placement model.
    """
    if not predictor.is_trained or not predictor.metrics:
        predictor.train_model(db)
    return predictor.get_metrics()

@router.get("/feature-importance")
def get_feature_importance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get native Random Forest Gini feature importances driving placement predictions.
    """
    if not predictor.is_trained or not predictor.feature_importance:
        predictor.train_model(db)
    return {
        "feature_importance": predictor.get_feature_importance(),
        "explanations": {
            "cgpa": "Cumulative Grade Point Average across all semesters",
            "coding_score": "Aggregated LeetCode, CodeChef, and HackerRank competitive programming score",
            "attendance": "Academic attendance percentage",
            "num_skills": "Total verified technical skills listed on profile",
            "num_projects": "Number of portfolio and academic projects",
            "backlogs": "Current standing backlogs (negative placement factor)",
            "num_certs": "Number of professional certifications"
        }
    }

@router.get("/student-report/{student_id}")
def get_ai_student_report(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get full predictive AI audit for a student (Readiness, Probability, Skill Gaps, matching companies).
    """
    student = enforce_student_scope(current_user, student_id, db, "VIEW")

    report = predictor.evaluate_student(student, db)
    resume_analysis = predictor.calculate_resume_score(student)
    
    return {
        "student_id": student.id,
        "name": student.user.name,
        "readiness_score": report["readiness_score"],
        "placement_probability": report["placement_probability"],
        "decision_threshold": report.get("decision_threshold", 0.30),
        "is_placement_likely": report.get("is_placement_likely", False),
        "predicted_status": report.get("predicted_status", "At Risk"),
        "skills_gap": report["skills_gap"],
        "recommended_skills": report["recommended_skills"],
        "recommended_projects": report["recommended_projects"],
        "recommended_certifications": report["recommended_certifications"],
        "matching_companies": report["matching_companies"],
        "explanation": report["explanation"],
        "at_risk": report["at_risk"],
        "risk_reason": report["risk_reason"],
        "improvement_tips": report["improvement_tips"],
        "resume_quality": resume_analysis,
        "cohort_readiness_cutoff": report.get("cohort_readiness_cutoff", 87.14),
        "cohort_percentile": report.get("cohort_percentile", None),
        "preparation_tier": report.get("preparation_tier", "Making Progress")
    }

@router.get("/feedback-sentiment")
def get_feedback_mining_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Aggregate NLP details across all student interview feedback logs.
    Computes sentiment proportions, top subjects, question difficulty levels, and word cloud tags.
    """
    feedbacks = db.query(Feedback).all()
    if not feedbacks:
        return {
            "total_feedbacks": 0,
            "average_difficulty": 0.0,
            "sentiment_summary": {"positive": 0, "neutral": 0, "negative": 0},
            "topic_distribution": [],
            "frequent_keywords": [],
            "common_bottlenecks": []
        }

    total_fb = len(feedbacks)
    total_diff = sum([f.difficulty_rating for f in feedbacks])
    avg_diff = round(total_diff / total_fb, 2)

    # Sentiment distribution
    pos, neu, neg = 0, 0, 0
    topic_counts = {}
    word_list = []
    keyword_counts = {}

    # List of English stop words to filter out from Word Cloud
    stop_words = {
        "the", "and", "a", "of", "to", "in", "is", "was", "for", "on", "it", "with", "as", "by", "an", "at",
        "they", "their", "them", "he", "she", "i", "we", "you", "me", "my", "our", "were", "had", "have", "has",
        "about", "also", "asked", "interview", "questions", "round", "very", "panel", "experience", "felt",
        "some", "but", "so", "this", "that", "from", "be", "been", "would", "could", "should", "not", "no"
    }

    for f in feedbacks:
        # Sentiment
        if f.sentiment_score > 0.15:
            pos += 1
        elif f.sentiment_score < -0.15:
            neg += 1
        else:
            neu += 1

        # Topic
        topic = f.topic_analysis or "General"
        topic_counts[topic] = topic_counts.get(topic, 0) + 1

        # Tokenize text for word cloud word counts
        cleaned = re.sub(r"[^\w\s]", " ", f.experience_text.lower())
        words = [w for w in cleaned.split() if w not in stop_words and len(w) > 2]
        word_list.extend(words)

        # Keyword counts
        if f.extracted_keywords:
            kws = [k.strip() for k in f.extracted_keywords.split(",")]
            for kw in kws:
                if kw:
                    keyword_counts[kw] = keyword_counts.get(kw, 0) + 1

    # Format topic distribution
    topic_dist = [{"topic": k, "count": v} for k, v in topic_counts.items()]
    
    # Format word cloud (top 25 words)
    top_words = Counter(word_list).most_common(25)
    word_cloud = [{"text": word, "value": count} for word, count in top_words]

    # Format frequent keywords (top 10 tech subjects)
    top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    freq_keywords = [{"keyword": k, "count": v} for k, v in top_keywords]

    # Dynamic common rejection reasons/bottlenecks based on negative feedback keywords
    neg_feedbacks = [f for f in feedbacks if f.sentiment_score < 0.0]
    bottlenecks_list = []
    
    for nf in neg_feedbacks:
        # Check text match for specific struggles
        text_lower = nf.experience_text.lower()
        if "dynamic programming" in text_lower or "dp" in text_lower or "knapsack" in text_lower:
            bottlenecks_list.append("Struggling with Dynamic Programming / Memoization (Knapsack)")
        elif "recursion" in text_lower or "recursive" in text_lower:
            bottlenecks_list.append("Difficulty establishing recursion base cases & stack tracking")
        elif "sql" in text_lower or "joins" in text_lower or "indexing" in text_lower:
            bottlenecks_list.append("Inability to construct complex SQL Joins or explain indexes")
        elif "networking" in text_lower or "tcp" in text_lower or "udp" in text_lower:
            bottlenecks_list.append("Weak understanding of Computer Networks protocols (TCP/IP)")
        elif "system design" in text_lower or "scaling" in text_lower:
            bottlenecks_list.append("Lack of experience scaling microservices / System Design")
        else:
            bottlenecks_list.append("Nervousness & poor explanation of project core architectures")

    # Count top bottleneck occurrences
    bottlenecks_agg = Counter(bottlenecks_list).most_common(5)
    common_bottlenecks = [{"bottleneck": k, "count": v} for k, v in bottlenecks_agg]

    if not common_bottlenecks:
        common_bottlenecks = [
            {"bottleneck": "Dynamic Programming & complex array operations", "count": 1},
            {"bottleneck": "Explaining complex projects architecture", "count": 1}
        ]

    # Run Semantic Grouping Miner (Req 9)
    themes = feedback_miner.group_feedback(feedbacks)

    return {
        "total_feedbacks": total_fb,
        "average_difficulty": avg_diff,
        "sentiment_summary": {
            "positive": pos,
            "neutral": neu,
            "negative": neg,
            "positive_pct": round(pos / total_fb * 100, 1),
            "neutral_pct": round(neu / total_fb * 100, 1),
            "negative_pct": round(neg / total_fb * 100, 1),
        },
        "topic_distribution": topic_dist,
        "word_cloud": word_cloud,
        "frequent_keywords": freq_keywords,
        "common_bottlenecks": common_bottlenecks,
        "themes": themes
    }

@router.get("/feedbacks")
def get_all_feedbacks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in ["admin", "faculty", "hod", "tnp"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    feedbacks = db.query(Feedback).all()
    results = []
    for f in feedbacks:
        results.append({
            "id": f.id,
            "student_name": f.interview.student.user.name if f.interview and f.interview.student else "Anonymous Student",
            "company_name": f.interview.application.drive.company.name if f.interview and f.interview.application and f.interview.application.drive else "Unknown Company",
            "role": f.interview.application.drive.role if f.interview and f.interview.application and f.interview.application.drive else "Job Applicant",
            "experience_text": f.experience_text,
            "questions_asked": f.questions_asked,
            "difficulty_rating": f.difficulty_rating,
            "preparation_time": f.preparation_time,
            "sentiment_score": f.sentiment_score,
            "topic_analysis": f.topic_analysis,
            "extracted_keywords": f.extracted_keywords,
            "created_at": f.interview.interview_date.strftime('%Y-%m-%d') if f.interview and f.interview.interview_date else "Recent"
        })
    return results

@router.get("/drives/{drive_id}/feedback-summary")
def get_drive_feedback_summary(
    drive_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get consolidated feedback report for a specific placement drive.
    Aggregates all student feedback associated with the drive:
    1. Participation (attendees, feedback count, response rate)
    2. Overall interview experience (experience summary, sentiment tone breakdown, average rating)
    3. Topics asked (ranked topic distribution with percentages)
    4. Questions asked (duplicate/common questions normalized and frequency counted)
    5. Difficulty distribution (Easy, Moderate, Difficult counts and percentages)
    6. Common interview areas (Programming, DSA, DBMS, OOP, OS, Networks, Aptitude, HR)
    7. Student experiences and suggestions (senior advice, identified bottlenecks, recurring themes)
    Strictly preserves student anonymity and enforces department-scoped RBAC.
    """
    if current_user.role not in ["admin", "faculty", "hod", "tnp", "student"]:
        raise HTTPException(status_code=403, detail="Access denied")

    drive = db.query(PlacementDrive).filter(PlacementDrive.id == drive_id).first()
    if not drive:
        raise HTTPException(status_code=404, detail="Placement drive not found")

    # Enforce department scoping for Faculty/HOD
    if current_user.role in ["faculty", "hod"]:
        dept_code = (
            current_user.faculty_profile.department.code.upper()
            if current_user.faculty_profile and current_user.faculty_profile.department
            else ""
        )
        allowed = [d.strip().upper() for d in (drive.allowed_depts or "").split(",") if d.strip()]
        if "ALL" not in allowed and dept_code not in allowed:
            from backend.app.auth import verify_permission
            scope_info = verify_permission(current_user, "Placement Drives", "VIEW", db)
            scope = scope_info.get("scope")
            scope_val = str(scope_info.get("scope_value", "")).upper()
            if scope != "ALL" and not any(d in allowed for d in [scope_val, dept_code]):
                raise HTTPException(status_code=403, detail="Access denied: placement drive outside authorized department scope")

    company_name = drive.company.name if drive.company else "Unknown Company"

    # Participation metrics
    applications = db.query(Application).filter(Application.drive_id == drive_id).all()
    interviews = db.query(Interview).join(Application).filter(Application.drive_id == drive_id).all()
    total_applicants = len(applications)
    interviewed_student_ids = {i.student_id for i in interviews}
    attended_students_count = len(interviewed_student_ids) if interviewed_student_ids else len(applications)

    feedbacks = (
        db.query(Feedback)
        .join(Interview, Feedback.interview_id == Interview.id)
        .join(Application, Interview.application_id == Application.id)
        .filter(Application.drive_id == drive_id)
        .all()
    )
    total_feedbacks = len(feedbacks)

    # Clean empty state when no feedback records exist for this drive
    if total_feedbacks == 0:
        return {
            "drive_id": drive.id,
            "company_name": company_name,
            "role": drive.role,
            "package_lpa": drive.package_lpa,
            "location": drive.location,
            "batch": drive.batch,
            "allowed_depts": drive.allowed_depts,
            "total_feedbacks": 0,
            "has_feedback": False,
            "has_sufficient_data": False,
            "participation": {
                "total_applicants": total_applicants,
                "attended_students_count": attended_students_count,
                "feedback_responses_count": 0,
                "total_feedbacks": 0,
                "candidates_attended_or_applied": attended_students_count,
                "response_rate_pct": 0.0
            },
            "message": "No candidate interview feedback records have been logged for this recruitment drive yet."
        }

    if total_feedbacks < 5:
        response_rate_pct = round((total_feedbacks / attended_students_count * 100), 1) if attended_students_count > 0 else 100.0
        return {
            "drive_id": drive.id,
            "company_name": company_name,
            "role": drive.role,
            "package_lpa": drive.package_lpa,
            "location": drive.location,
            "batch": drive.batch,
            "allowed_depts": drive.allowed_depts,
            "total_feedbacks": total_feedbacks,
            "min_required_threshold": 5,
            "has_feedback": True,
            "has_sufficient_data": False,
            "participation": {
                "total_applicants": total_applicants,
                "attended_students_count": attended_students_count,
                "feedback_responses_count": total_feedbacks,
                "total_feedbacks": total_feedbacks,
                "candidates_attended_or_applied": attended_students_count,
                "response_rate_pct": min(100.0, response_rate_pct)
            },
            "message": f"Not enough feedback yet for a detailed report ({total_feedbacks}/5 submissions received). At least 5 candidate submissions are required to generate aggregated interview intelligence."
        }

    # 1. Participation
    response_rate_pct = round((total_feedbacks / attended_students_count * 100), 1) if attended_students_count > 0 else 100.0
    participation = {
        "total_applicants": total_applicants,
        "attended_students_count": attended_students_count,
        "feedback_responses_count": total_feedbacks,
        "total_feedbacks": total_feedbacks,
        "candidates_attended_or_applied": attended_students_count,
        "response_rate_pct": min(100.0, response_rate_pct)
    }

    # 2. Overall Interview Experience & Ratings
    total_diff = sum(f.difficulty_rating or 3 for f in feedbacks)
    avg_diff = round(total_diff / total_feedbacks, 2)

    total_rating = sum(f.rating or f.difficulty_rating or 3 for f in feedbacks)
    avg_rating = round(total_rating / total_feedbacks, 2)

    # Sentiment distribution
    pos = sum(1 for f in feedbacks if (f.sentiment_score or 0.0) > 0.15)
    neg = sum(1 for f in feedbacks if (f.sentiment_score or 0.0) < -0.15)
    neu = total_feedbacks - pos - neg

    sentiment_summary = {
        "positive": pos,
        "neutral": neu,
        "negative": neg,
        "positive_pct": round(pos / total_feedbacks * 100, 1),
        "neutral_pct": round(neu / total_feedbacks * 100, 1),
        "negative_pct": round(neg / total_feedbacks * 100, 1)
    }

    # Semantic clustering via feedback_miner
    themes = feedback_miner.group_feedback(feedbacks)

    # 3. Difficulty Distribution (Easy: 1-2, Moderate: 3, Difficult: 4-5)
    easy_count = sum(1 for f in feedbacks if (f.difficulty_rating or 3) <= 2)
    mod_count = sum(1 for f in feedbacks if (f.difficulty_rating or 3) == 3)
    diff_count = sum(1 for f in feedbacks if (f.difficulty_rating or 3) >= 4)
    difficulty_distribution = {
        "easy": easy_count,
        "easy_count": easy_count,
        "easy_pct": round(easy_count / total_feedbacks * 100, 1),
        "moderate": mod_count,
        "moderate_count": mod_count,
        "moderate_pct": round(mod_count / total_feedbacks * 100, 1),
        "difficult": diff_count,
        "difficult_count": diff_count,
        "difficult_pct": round(diff_count / total_feedbacks * 100, 1),
        "average_difficulty": avg_diff,
        "average_score": avg_diff,
        "total_rated": total_feedbacks
    }

    # 4. Questions Asked (grouped and counted by frequency)
    def normalize_question(q_str: str) -> str:
        q_norm = q_str.strip()
        q_lower = q_norm.lower()
        if "binary search tree" in q_lower or "bst" in q_lower:
            return "Binary Search Tree Construction & Traversals"
        elif "dynamic programming" in q_lower or "dp" in q_lower or "knapsack" in q_lower:
            return "Dynamic Programming (Knapsack & Subsequences)"
        elif "recursion" in q_lower or "recursive" in q_lower:
            return "Recursion & Call Stack Management"
        elif "sql" in q_lower and "join" in q_lower:
            return "SQL Joins & Complex Aggregate Queries"
        elif "index" in q_lower and ("sql" in q_lower or "db" in q_lower or "table" in q_lower):
            return "Database Indexing & Query Optimization"
        elif "dbms" in q_lower or "normalization" in q_lower:
            return "DBMS Architecture & Normalization Forms"
        elif "oop" in q_lower or "polymorphism" in q_lower or "inheritance" in q_lower:
            return "OOP Concepts (Inheritance & Polymorphism)"
        elif "deadlock" in q_lower or "semaphore" in q_lower:
            return "OS Deadlocks, Semaphore & Concurrency"
        elif "os" in q_lower or "operating system" in q_lower:
            return "Operating System Fundamentals & Process States"
        elif "network" in q_lower or "tcp" in q_lower or "udp" in q_lower:
            return "Computer Networks (TCP 3-way Handshake vs UDP)"
        elif "project" in q_lower:
            return "Academic Project Architecture & Design Defense"
        elif "hr" in q_lower or "relocation" in q_lower or "situation" in q_lower:
            return "HR Behavioral Scenarios & Career Aspirations"
        return q_norm

    question_counts = Counter()
    for f in feedbacks:
        if f.questions_asked:
            parts = re.split(r"[,;\n]+", f.questions_asked)
            for p in parts:
                p_clean = p.strip()
                if len(p_clean) >= 2 and not p_clean.isdigit():
                    grouped_q = normalize_question(p_clean)
                    question_counts[grouped_q] += 1

    top_questions = [
        {
            "question": q,
            "count": c,
            "frequency": c,
            "percentage": round(c / total_feedbacks * 100, 1),
            "frequency_pct": round(c / total_feedbacks * 100, 1),
            "round": "Technical" if any(k in q.lower() for k in ["tree", "sql", "code", "oop", "os", "network", "dbms"]) else "Technical / HR"
        }
        for q, c in question_counts.most_common(12)
    ]

    # 5. Topics Asked
    topic_counts = Counter()
    for f in feedbacks:
        topic = (f.topic_analysis or "").strip()
        if topic:
            topic_counts[topic] += 1
        else:
            topic_counts["General Technical Evaluation"] += 1

    topic_distribution = [
        {"topic": t, "count": c, "frequency": c, "percentage": round(c / total_feedbacks * 100, 1)}
        for t, c in topic_counts.most_common(10)
    ]

    # 6. Common Interview Areas (only when actually present in feedback)
    area_keywords = {
        "Programming": ["programming", "python", "java", "c++", "c programming", "coding"],
        "Data Structures": ["data structures", "dsa", "tree", "linked list", "recursion", "stack", "queue", "graph", "binary search tree", "dynamic programming", "knapsack"],
        "DBMS": ["dbms", "sql", "database", "joins", "indexes", "normalization", "query"],
        "OOP": ["oop", "oops", "inheritance", "polymorphism", "encapsulation", "abstraction", "classes"],
        "OS": ["os", "operating system", "deadlock", "process", "threading", "semaphore", "memory"],
        "Computer Networks": ["computer networks", "networking", "network", "tcp", "udp", "ip", "protocols", "handshake"],
        "Aptitude": ["aptitude", "quant", "reasoning", "puzzle", "math"],
        "HR / Behavioral": ["hr", "behavioral", "relocation", "strengths", "situation", "culture", "leadership"]
    }
    interview_areas_counts = Counter()
    for f in feedbacks:
        combined_text = f"{(f.questions_asked or '')} {(f.topic_analysis or '')} {(f.experience_text or '')} {(f.extracted_keywords or '')}".lower()
        for area_name, kws in area_keywords.items():
            if any(kw in combined_text for kw in kws):
                interview_areas_counts[area_name] += 1

    common_interview_areas = [
        {"area": a, "count": cnt, "percentage": round(cnt / total_feedbacks * 100, 1)}
        for a, cnt in interview_areas_counts.most_common()
        if cnt > 0
    ]

    # 7. Student Experiences & Suggestions (privacy preserved)
    neg_feedbacks = [f for f in feedbacks if (f.sentiment_score or 0.0) < 0.0 or (f.difficulty_rating or 0) >= 4]
    bottlenecks_list = []
    for nf in neg_feedbacks:
        text_lower = (nf.experience_text or "").lower()
        if "dynamic programming" in text_lower or "dp" in text_lower or "knapsack" in text_lower:
            bottlenecks_list.append("Dynamic Programming & complex memoization")
        elif "recursion" in text_lower or "recursive" in text_lower or "tree" in text_lower:
            bottlenecks_list.append("Tree traversals, recursion base cases & stack depth")
        elif "sql" in text_lower or "joins" in text_lower or "indexing" in text_lower:
            bottlenecks_list.append("Relational SQL indexing & multi-table join optimization")
        elif "networking" in text_lower or "tcp" in text_lower or "udp" in text_lower:
            bottlenecks_list.append("Computer Networks protocols (TCP vs UDP) & handshakes")
        elif "system design" in text_lower or "scaling" in text_lower or "architecture" in text_lower:
            bottlenecks_list.append("System architecture scalability & trade-offs")
        elif "pointer" in text_lower or "memory" in text_lower:
            bottlenecks_list.append("Pointer arithmetic & memory management")
        else:
            bottlenecks_list.append("Deep technical defense of final year academic project")

    if not bottlenecks_list:
        bottlenecks_list = ["Project architecture explanation under panel pressure"]

    common_bottlenecks = [
        {"bottleneck": b, "count": cnt}
        for b, cnt in Counter(bottlenecks_list).most_common(5)
    ]

    suggestions_counts = Counter()
    for f in feedbacks:
        if f.suggestions and len(f.suggestions.strip()) > 5:
            suggestions_counts[f.suggestions.strip()] += 1

    senior_advice = [
        {"advice": s, "mentions": cnt, "count": cnt}
        for s, cnt in suggestions_counts.most_common(6)
    ]

    top_area_names = [a["area"] for a in common_interview_areas[:3]]
    experience_summary = (
        f"Consolidated analysis of {total_feedbacks} candidate evaluations for {company_name} ({drive.role}). "
        f"Student sentiment is {sentiment_summary['positive_pct']}% positive with an average difficulty rating of {avg_diff} / 5.0. "
        f"Key assessed interview domains include {', '.join(top_area_names) if top_area_names else 'General Evaluation'}."
    )

    common_observations = [
        f"Overall feedback is predominantly constructive ({sentiment_summary['positive_pct']}% positive).",
        f"Interview difficulty was evaluated at an average of {avg_diff} / 5.0.",
        f"Assessed questions centered primarily on {', '.join(top_area_names) if top_area_names else 'Technical Core'}."
    ]

    overall_experience = {
        "summary": experience_summary,
        "sentiment_distribution": sentiment_summary,
        "common_observations": common_observations,
        "average_difficulty": avg_diff,
        "average_rating": avg_rating
    }

    student_suggestions = {
        "top_advice_notes": senior_advice,
        "recurring_blockers": common_bottlenecks,
        "anonymity_preserved": True
    }

    return {
        "drive_id": drive.id,
        "company_name": company_name,
        "role": drive.role,
        "package_lpa": drive.package_lpa,
        "location": drive.location,
        "batch": drive.batch,
        "allowed_depts": drive.allowed_depts,
        "total_feedbacks": total_feedbacks,
        "has_feedback": True,
        "has_sufficient_data": True,
        "participation": participation,
        "experience_summary": experience_summary,
        "overall_experience": overall_experience,
        "average_difficulty": avg_diff,
        "average_rating": avg_rating,
        "sentiment_summary": sentiment_summary,
        "difficulty_distribution": difficulty_distribution,
        "common_interview_areas": common_interview_areas,
        "topic_distribution": topic_distribution,
        "topics_asked": topic_distribution,
        "top_questions": top_questions,
        "questions_asked": top_questions,
        "common_bottlenecks": common_bottlenecks,
        "senior_advice": senior_advice,
        "student_suggestions": student_suggestions,
        "themes": themes
    }


# 1. RESUME SCANNER & UPLOAD

@router.post("/resume/upload")
async def upload_resume(
    file: UploadFile = File(...),
    drive_id: Optional[int] = Form(None),
    drive_id_query: Optional[int] = Query(None, alias="drive_id"),
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """
    Upload resume, extract text using scan modules, compute score and save details in Student record.
    If drive_id is provided, scores against the specific drive.
    If drive_id is omitted, scores against the General Industry Software Baseline.
    """
    target_drive_id = drive_id if drive_id is not None else drive_id_query
    content = await file.read()
    extracted_text = resume_scanner.extract_text(content, file.filename)
    
    if not extracted_text or len(extracted_text.strip()) < 50:
        raise HTTPException(
            status_code=400,
            detail="Not enough text could be extracted from this file — please upload a text-based PDF or Word document"
        )
    
    # 1. Baseline standard
    GENERAL_INDUSTRY_BASELINE = {
        "required_skills": "Python, Java, SQL, React, JavaScript, Data Structures",
        "role": "Software Engineer (Industry Standard)",
        "responsibilities": "Design, develop, test, and maintain robust software applications and services."
    }
    
    jd_details = GENERAL_INDUSTRY_BASELINE
    comparison_source = "General Industry Software Baseline"
    
    if target_drive_id:
        drive = db.query(PlacementDrive).filter(PlacementDrive.id == target_drive_id).first()
        if drive:
            jd_details = {
                "required_skills": drive.required_skills or "Python, Java, SQL, React, JavaScript, Data Structures",
                "role": drive.role or "Software Engineer",
                "responsibilities": drive.responsibilities or "General software engineering duties."
            }
            comparison_source = f"{drive.company.name} - {drive.role}"
        
    analysis = resume_scanner.analyze_resume(extracted_text, jd_details)
    analysis["comparison_target"] = comparison_source
    analysis["skills_matched"] = analysis.get("matching_skills", [])
    
    # Save parameters in student profile
    current_student.resume_text = extracted_text
    current_student.resume_ats_score = analysis["ats_score"]
    current_student.resume_analysis_json = json.dumps(analysis)
    current_student.resume_path = f"resumes/{current_student.id}_{file.filename}"
    db.commit()
    db.refresh(current_student)
    
    return {
        "message": "Resume uploaded and analyzed successfully!",
        "comparison_target": comparison_source,
        "ats_score": current_student.resume_ats_score,
        "analysis": analysis
    }


# 2. JOB MATCH DETAILS

@router.get("/job-match/{drive_id}")
def get_student_job_match(
    drive_id: int,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Compare student profile details against targeted recruitment drive Job Description."""
    drive = db.query(PlacementDrive).filter(PlacementDrive.id == drive_id).first()
    if not drive:
        raise HTTPException(status_code=404, detail="Recruitment drive not found")
        
    report = predictor.calculate_job_match(current_student, drive)
    return report

# 3. TAILORED PREPARATION ROADMAP

@router.get("/prep-roadmap/{drive_id}")
def get_preparation_roadmap(
    drive_id: int,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Generate week-by-week preparation roadmap tailored to candidate missing skills and target recruiter."""
    drive = db.query(PlacementDrive).filter(PlacementDrive.id == drive_id).first()
    if not drive:
        raise HTTPException(status_code=404, detail="Recruitment drive not found")
        
    roadmap = predictor.generate_preparation_roadmap(current_student, drive)
    return roadmap

# 4. INSTITUTIONAL INSIGHTS BOARD

@router.get("/insights")
def get_institutional_ai_insights(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Aggregate system logs and predictions to compile coordinator insights reports."""
    # Only faculty and admins can view institutional insights
    if current_user.role not in ["faculty", "admin"]:
        raise HTTPException(status_code=403, detail="Access denied")

    students = db.query(Student).all()
    drives = db.query(PlacementDrive).all()
    feedbacks = db.query(Feedback).all()

    if not students:
        return {"message": "No students registered yet"}

    # Branch-wise readiness rankings
    branch_readiness = {}
    for s in students:
        code = s.department.code
        branch_readiness[code] = branch_readiness.get(code, []) + [s.readiness_score]
        
    branch_readiness_avg = [
        {"dept_code": k, "avg_readiness": round(sum(v)/len(v), 1)} 
        for k, v in branch_readiness.items()
    ]
    branch_readiness_avg = sorted(branch_readiness_avg, key=lambda x: x["avg_readiness"], reverse=True)

    # Demanded skills from active drives
    skill_counts = {}
    for d in drives:
        if d.required_skills:
            for s in d.required_skills.split(","):
                s_clean = s.strip().upper()
                if s_clean:
                    skill_counts[s_clean] = skill_counts.get(s_clean, 0) + 1
                    
    demanded_skills = [
        {"skill": k, "demand_count": v} 
        for k, v in sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:8]
    ]

    # Students most likely to get selected
    likely_selected = sorted(
        [s for s in students if s.batch == "2026" and s.status != "Placed"],
        key=lambda x: x.placement_probability,
        reverse=True
    )[:10]
    
    likely_selected_list = [
        {
            "id": s.id,
            "name": s.user.name,
            "dept_code": s.department.code,
            "cgpa": s.cgpa,
            "probability": round(s.placement_probability * 100, 1)
        }
        for s in likely_selected
    ]

    # Students at risk
    at_risk_list = [
        {
            "id": s.id,
            "name": s.user.name,
            "dept_code": s.department.code,
            "cgpa": s.cgpa,
            "readiness_score": s.readiness_score,
            "status": s.status
        }
        for s in students if s.status == "At Risk" and s.batch == "2026"
    ][:10]

    # Rejection topics from negative feedback
    difficulty_counts = {}
    for f in feedbacks:
        if f.difficulty_rating >= 4:
            comp_name = f.interview.application.drive.company.name
            difficulty_counts[comp_name] = difficulty_counts.get(comp_name, 0) + 1
            
    difficult_companies = [
        {"company": k, "hard_rounds_count": v} 
        for k, v in sorted(difficulty_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    ]

    return {
        "branch_readiness_avg": branch_readiness_avg,
        "demanded_skills": demanded_skills,
        "students_likely_selected": likely_selected_list,
        "students_at_risk": at_risk_list,
        "difficult_companies": difficult_companies
    }
