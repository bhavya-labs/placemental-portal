import re

def fix_routes():
    file_path = 'backend/app/routers/students.py'
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the correction requests block
    pattern_correction = r"(# CORRECTION REQUESTS.*?\n)(?=\n# STUDENT TIMELINE|\n# STUDENT 360)"
    match_correction = re.search(pattern_correction, content, re.DOTALL)
    if not match_correction:
        print("ERROR: Could not find correction requests block")
        return
    correction_block = match_correction.group(1)

    # Find the student timeline block
    pattern_timeline = r"(# STUDENT TIMELINE.*?\n)(?=\n# STUDENT 360)"
    match_timeline = re.search(pattern_timeline, content, re.DOTALL)
    if not match_timeline:
        print("ERROR: Could not find timeline block")
        return
    timeline_block = match_timeline.group(1)

    # Remove the blocks from the bottom of the content
    content_clean = content.replace(correction_block, "").replace(timeline_block, "")

    # Insert the blocks right before @router.get("/{student_id}")
    insertion_point = '@router.get("/{student_id}")'
    if insertion_point not in content_clean:
        print("ERROR: Could not find insertion point get_student_by_id")
        return

    replacement = correction_block + "\n" + timeline_block + "\n" + insertion_point
    content_fixed = content_clean.replace(insertion_point, replacement)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content_fixed)

    print("SUCCESS: Routes reordered successfully!")

if __name__ == '__main__':
    fix_routes()
