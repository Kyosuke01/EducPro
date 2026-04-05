import re
import os

files_to_check = {
    'backend/app/routes/attendance.py': [18, 116],
    'backend/app/routes/auth.py': [85, 208, 267],
    'backend/app/routes/classes.py': [17, 105],
    'backend/app/routes/edt.py': [28, 114],
    'backend/app/routes/grades.py': [107],
    'backend/app/routes/messages.py': [24, 40, 104, 248, 280],
}

for filepath, line_nums in files_to_check.items():
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            lines = f.readlines()
        for ln in line_nums:
            if ln <= len(lines):
                print(f"{filepath}:{ln}")
                print(f"  {lines[ln-1].rstrip()}")
