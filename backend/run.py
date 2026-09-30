import os
import sys
import uvicorn

# Determine the project root directory
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

if __name__ == "__main__":
    print(f"Starting FastAPI server from directory: {project_root}")
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
