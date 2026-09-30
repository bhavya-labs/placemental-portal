import os
import re

report_path = 'FINAL_PROJECT_REPORT.md'
with open(report_path, 'r', encoding='utf-8') as f:
    text = f.read()

lines = text.splitlines()
words = text.split()
sections = re.findall(r'^##\s+\d+\..*', text, flags=re.MULTILINE)

print(f"File Path: {os.path.abspath(report_path)}")
print(f"Total Bytes: {len(text.encode('utf-8'))}")
print(f"Total Lines: {len(lines)}")
print(f"Approximate Word Count: {len(words)}")
print(f"Total Main Numbered Sections: {len(sections)}")
print("Sections identified:")
for s in sections:
    print("  -", s)
