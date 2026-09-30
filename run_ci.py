#!/usr/bin/env python
"""
AP-CPIP Local CI & Verification Runner
======================================
Executes comprehensive project validation suitable for viva demonstrations:
1. Alembic Database Migration check
2. Phase 1-3 Security & Database Regression checks
3. Pytest Full Test Suite (20 unit/integration tests)
"""

import os
import sys
import subprocess
from pathlib import Path

def run_step(title, command, cwd=None):
    print("\n" + "=" * 65)
    print(f" CI STEP: {title}")
    print("=" * 65)
    res = subprocess.run(command, cwd=cwd or str(Path(__file__).parent), shell=True)
    if res.returncode != 0:
        print(f"\n[FAILED] Step '{title}' failed with exit code {res.returncode}")
        sys.exit(res.returncode)
    print(f"[PASSED] Step '{title}' completed successfully.")

def main():
    project_root = Path(__file__).resolve().parent
    print("\n" + "#" * 65)
    print(" AP-CPIP LOCAL CONTINUOUS INTEGRATION (CI) RUNNER")
    print("#" * 65)

    # Step 1: Alembic Migrations
    run_step("Alembic Database Schema Migration Check", "python -m alembic current")

    # Step 2: Phase 1 Security Hardening Check
    run_step("Security Hardening & Rate Limiting Audit", "python tests/test_phase1_security.py")

    # Step 3: Phase 2 Database & Pagination Audit
    run_step("Database Indexes & Pagination Audit", "python tests/test_phase2_database.py")

    # Step 4: Phase 3 ML Rigor Audit
    run_step("ML Rigor (Train/Test Split & Metrics) Audit", "python tests/test_phase3_ml.py")

    # Step 5: Pytest Automated Test Suite
    run_step("Pytest Full Test Suite (27 Test Cases)", "python -m pytest")

    print("\n" + "#" * 65)
    print(" [SUCCESS] ALL CI CHECKS & PYTEST SUITES PASSED CLEANLY!")
    print("#" * 65 + "\n")

if __name__ == "__main__":
    main()
