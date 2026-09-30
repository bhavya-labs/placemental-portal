#!/usr/bin/env bash
# Exit immediately on error
set -o errexit

echo "========================================="
echo " Building Placement Intelligence Platform "
echo "========================================="

# 1. Upgrade pip and install Python backend dependencies
echo "[1/4] Installing Python backend dependencies..."
pip install --upgrade pip
pip install -r backend/requirements.txt

# 2. Build React frontend application
echo "[2/4] Building React frontend application..."
cd frontend
npm install --no-audit --no-fund
npm run build
cd ..

# 3. Apply Alembic migrations to database
echo "[3/4] Running database migrations..."
python -m alembic upgrade head

# 4. Success confirmation
echo "[4/4] Build completed successfully! Ready for launch."
