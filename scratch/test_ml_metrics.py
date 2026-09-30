import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from backend.app.database import SessionLocal
from backend.app.ml.predictor import predictor
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import pandas as pd
import numpy as np

db = SessionLocal()
try:
    students = db.query(predictor.Student if hasattr(predictor, 'Student') else None or __import__('backend.app.models', fromlist=['Student']).Student).all()
    data = []
    labels = []
    for s in students:
        feat = predictor._extract_features(s)
        data.append(list(feat.values()))
        labels.append(1 if s.status == "Placed" else 0)

    X = np.array(data)
    y = np.array(labels)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    print(f"X_train shape: {X_train.shape}, X_test shape: {X_test.shape}")
    print(f"y_train distribution: {np.bincount(y_train)}, y_test distribution: {np.bincount(y_test)}")

    scaler = predictor.scaler
    scaler.fit(X_train)
    X_train_scaled = scaler.transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = predictor.model
    model.fit(X_train_scaled, y_train)

    y_pred = model.predict(X_test_scaled)
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    cm = confusion_matrix(y_test, y_pred)

    print("\n--- Model Evaluation on Test Set ---")
    print(f"Accuracy:  {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall:    {rec:.4f}")
    print(f"F1 Score:  {f1:.4f}")
    print("Confusion Matrix:\n", cm)

    feature_names = ["cgpa", "attendance", "backlogs", "num_skills", "num_projects", "num_certs", "coding_score"]
    importances = model.feature_importances_
    print("\n--- Feature Importances ---")
    for name, imp in sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True):
        print(f"  {name:15s}: {imp:.4f} ({imp*100:.1f}%)")

finally:
    db.close()
