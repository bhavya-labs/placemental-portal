import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

from backend.app.database import SessionLocal
from backend.app.models import Student
from backend.app.ml.predictor import predictor

db = SessionLocal()
try:
    students = db.query(Student).all()
    data = []
    labels = []
    for s in students:
        feat = predictor._extract_features(s)
        data.append(list(feat.values()))
        labels.append(1 if s.status == "Placed" else 0)

    X = np.array(data)
    y = np.array(labels)

    # Exact same 80/20 stratified split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # 1. Baseline: default weights
    rf_baseline = RandomForestClassifier(n_estimators=100, random_state=42)
    rf_baseline.fit(X_train_scaled, y_train)
    probs_baseline = rf_baseline.predict_proba(X_test_scaled)[:, 1]

    # 2. Balanced weights
    rf_balanced = RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42)
    rf_balanced.fit(X_train_scaled, y_train)
    probs_balanced = rf_balanced.predict_proba(X_test_scaled)[:, 1]

    def eval_threshold(probs, y_true, threshold=0.5):
        preds = (probs >= threshold).astype(int)
        acc = accuracy_score(y_true, preds)
        prec = precision_score(y_true, preds, zero_division=0)
        rec = recall_score(y_true, preds, zero_division=0)
        f1 = f1_score(y_true, preds, zero_division=0)
        cm = confusion_matrix(y_true, preds)
        tn, fp, fn, tp = cm.ravel()
        return {
            "threshold": threshold,
            "accuracy": acc,
            "precision": prec,
            "recall": rec,
            "f1": f1,
            "cm": cm,
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp)
        }

    res_baseline = eval_threshold(probs_baseline, y_test, 0.5)
    res_balanced_05 = eval_threshold(probs_balanced, y_test, 0.5)
    res_balanced_04 = eval_threshold(probs_balanced, y_test, 0.4)
    res_balanced_03 = eval_threshold(probs_balanced, y_test, 0.3)

    print("=== RESULTS COMPARISON ===")
    configs = [
        ("1. Baseline (default, th=0.5)", res_baseline),
        ("2. Balanced weights (th=0.5)", res_balanced_05),
        ("3. Balanced weights (th=0.4)", res_balanced_04),
        ("4. Balanced weights (th=0.3)", res_balanced_03)
    ]

    for name, r in configs:
        print(f"\nConfiguration: {name}")
        print(f"Accuracy:  {r['accuracy']:.4f} ({r['accuracy']*100:.2f}%)")
        print(f"Precision: {r['precision']:.4f} ({r['precision']*100:.2f}%)")
        print(f"Recall:    {r['recall']:.4f} ({r['recall']*100:.2f}%)")
        print(f"F1-Score:  {r['f1']:.4f} ({r['f1']*100:.2f}%)")
        print(f"Confusion Matrix: TN={r['tn']}, FP={r['fp']}, FN={r['fn']}, TP={r['tp']}")

    importances_balanced = rf_balanced.feature_importances_
    feat_names = ["cgpa", "attendance", "backlogs", "num_skills", "num_projects", "num_certs", "coding_score"]
    print("\nBalanced Feature Importances:")
    for fn, imp in sorted(zip(feat_names, importances_balanced), key=lambda x: x[1], reverse=True):
        print(f"  {fn:15s}: {imp:.4f} ({imp*100:.2f}%)")

finally:
    db.close()
