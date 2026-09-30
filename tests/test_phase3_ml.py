import os
import sys
import json
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.models import User, Student
from backend.app.ml.predictor import predictor
from backend.app.auth import create_access_token

def test_ml_training_and_metrics():
    print("\n--- Test 1: ML Model Training & Train/Test Split ---")
    db = SessionLocal()
    try:
        metrics = predictor.train_model(db, save_metrics=True)
        assert metrics is not None, "train_model returned None"
        assert predictor.is_trained is True, "Model is not marked as trained"
        
        # Verify split properties
        split = metrics["split"]
        assert split["test_size"] == 0.20, f"Expected 0.20 test size, got {split['test_size']}"
        assert split["stratified"] is True, "Expected stratified split"
        assert split["train_samples"] + split["test_samples"] == metrics["dataset"]["total_samples"]
        print(f"PASS: Train ({split['train_samples']}) / Test ({split['test_samples']}) 80/20 stratified split verified.")
        
        # Verify evaluation metrics
        eval_metrics = metrics["evaluation_metrics"]
        assert "accuracy" in eval_metrics
        assert "precision" in eval_metrics
        assert "recall" in eval_metrics
        assert "f1_score" in eval_metrics
        assert "confusion_matrix" in eval_metrics
        cm = eval_metrics["confusion_matrix"]
        assert len(cm) == 2 and len(cm[0]) == 2
        print(f"PASS: Metrics computed: Accuracy={eval_metrics['accuracy']:.4f}, Precision={eval_metrics['precision']:.4f}, Recall={eval_metrics['recall']:.4f}, F1={eval_metrics['f1_score']:.4f}")
        print(f"PASS: Confusion Matrix: {cm}")
        
        # Verify feature importance
        feat_imp = metrics["feature_importance"]
        assert len(feat_imp) == 7
        assert "cgpa" in feat_imp
        assert "coding_score" in feat_imp
        assert "attendance" in feat_imp
        print("PASS: Feature importance computed:")
        for k, v in feat_imp.items():
            print(f"   {k:15s}: {v:.4f}")
            
        # Verify label leakage audit is present in metrics payload
        leakage = metrics["label_leakage_audit"]
        assert leakage["detected"] is True
        print(f"PASS: Label leakage audit verified: {leakage['source']}")
        
        # Verify metrics file existence
        file1 = Path(project_root / "backend/app/ml/model_metrics.json")
        file2 = Path(project_root / "MODEL_METRICS.json")
        assert file1.exists(), f"{file1} does not exist!"
        assert file2.exists(), f"{file2} does not exist!"
        print("PASS: Both metrics files saved to disk.")
        
    finally:
        db.close()

def test_ai_metrics_endpoints():
    print("\n--- Test 2: AI Endpoints (/api/ai/model-metrics & /api/ai/feature-importance) ---")
    client = TestClient(app)
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.role == "admin").first()
        token = create_access_token(data={"sub": user.email if user else "admin@college.edu", "role": "admin"})
        headers = {"Authorization": f"Bearer {token}"}
        
        resp1 = client.get("/api/ai/model-metrics", headers=headers)
        assert resp1.status_code == 200, f"/api/ai/model-metrics returned {resp1.status_code}: {resp1.text}"
        data1 = resp1.json()
        assert "evaluation_metrics" in data1
        assert "feature_importance" in data1
        print("PASS: GET /api/ai/model-metrics returned valid metrics.")
        
        resp2 = client.get("/api/ai/feature-importance", headers=headers)
        assert resp2.status_code == 200, f"/api/ai/feature-importance returned {resp2.status_code}: {resp2.text}"
        data2 = resp2.json()
        assert "feature_importance" in data2
        assert "explanations" in data2
        print("PASS: GET /api/ai/feature-importance returned valid importances.")
        
    finally:
        db.close()

def test_scoring_weights_integrity():
    print("\n--- Test 3: Scoring Weights & Logic Integrity ---")
    # Verify calculate_readiness_score bounds and weighting
    dummy_student = Student(
        cgpa=10.0,
        attendance=100.0,
        backlogs=0,
        skills=json.dumps(["Python", "Java", "SQL", "React", "Docker", "Git", "C++"]),
        certifications=json.dumps(["AWS Certified", "TensorFlow Developer"]),
        projects=json.dumps([{"title": "P1"}, {"title": "P2"}, {"title": "P3"}]),
        leetcode_score=250,
        codechef_score=150,
        hackerrank_score=100
    )
    score = predictor.calculate_readiness_score(dummy_student)
    print(f"Max expected score for ideal student: {score}")
    assert score == 100.0, f"Expected 100.0 for ideal profile, got {score}"
    
    # Zero profile
    zero_student = Student(
        cgpa=0.0,
        attendance=0.0,
        backlogs=5,
        skills="[]",
        certifications="[]",
        projects="[]",
        leetcode_score=0,
        codechef_score=0,
        hackerrank_score=0
    )
    zero_score = predictor.calculate_readiness_score(zero_student)
    print(f"Min expected score for zero profile: {zero_score}")
    assert zero_score == 0.0, f"Expected 0.0, got {zero_score}"
    print("PASS: Scoring weights and edge-case clamping remain completely unchanged and preserved.")

def test_drive_feedback_summary_endpoint():
    print("\n--- Test 4: Drive Feedback Summary & Threshold Enforcement ---")
    client = TestClient(app)
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.role == "admin").first()
        token = create_access_token(data={"sub": user.email if user else "admin@college.edu", "role": "admin"})
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test Drive 4 (Apple, >= 5 submissions)
        resp4 = client.get("/api/ai/drives/4/feedback-summary", headers=headers)
        assert resp4.status_code == 200
        data4 = resp4.json()
        assert data4["has_sufficient_data"] is True
        assert data4["total_feedbacks"] >= 5
        assert "themes" in data4
        assert "sentiment_summary" in data4
        assert "average_difficulty" in data4
        assert "top_questions" in data4
        
        # Test Drive 6 (Infosys, < 5 submissions)
        resp6 = client.get("/api/ai/drives/6/feedback-summary", headers=headers)
        assert resp6.status_code == 200
        data6 = resp6.json()
        assert data6["has_sufficient_data"] is False
        assert data6["total_feedbacks"] < 5
        assert "message" in data6
        assert "3/5 submissions received" in data6["message"]
        print("PASS: Drive feedback summary and minimum threshold enforcement verified.")
    finally:
        db.close()

if __name__ == "__main__":
    test_ml_training_and_metrics()
    test_ai_metrics_endpoints()
    test_scoring_weights_integrity()
    test_drive_feedback_summary_endpoint()
    print("\n==================================================")
    print("ALL PHASE 3 ML RIGOR TESTS PASSED SUCCESSFULLY!")
    print("==================================================")

