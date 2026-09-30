import os
import re

terms = [
    "ai readiness",
    "sentiment miner",
    "ml outcome",
    "retrain ml",
    "commit changes",
    "sms gateway",
    "model prediction",
    "ai-generated",
    "ai feedback",
    "ai audit",
    "ai report",
    "ai insights",
    "ai recommendations"
]

frontend_dir = "frontend/src"
matches = []

for root, dirs, files in os.walk(frontend_dir):
    for file in files:
        if file.endswith(('.ts', '.tsx', '.html')):
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                for line_no, line in enumerate(lines, 1):
                    line_lower = line.lower()
                    for term in terms:
                        if term in line_lower:
                            matches.append((path, line_no, term, line.strip()))

print(f"Total jargon matches found: {len(matches)}")
for m in matches:
    print(f"{m[0]}:{m[1]} [{m[2]}] -> {m[3][:100]}")
