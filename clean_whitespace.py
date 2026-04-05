import re
import sys

files = [
    "backend/app/__init__.py",
    "backend/app/rbac.py",
    "backend/app/routes/attendance.py",
    "backend/app/routes/grades.py",
    "backend/app/routes/users.py"
]

for filepath in files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove trailing whitespace on blank lines
    content = re.sub(r'^ +$', '', content, flags=re.MULTILINE)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✓ Cleaned {filepath}")
