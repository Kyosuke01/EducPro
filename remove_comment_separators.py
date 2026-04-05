import re
import os

# Files to clean
files = [
    "backend/app/__init__.py",
    "backend/app/routes/users.py",
    "backend/app/routes/auth.py",
    "backend/app/routes/classes.py",
    "backend/app/routes/attendance.py",
    "backend/app/routes/edt.py",
    "backend/app/routes/grades.py",
    "backend/app/routes/messages.py",
    "frontend/app.py",
]

# Pattern to remove: lines that are only dashes/spaces in comments
pattern = re.compile(r'^\s*#\s*[─\-=\s]+\s*$', re.MULTILINE)

for filepath in files:
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove separator lines
        cleaned = pattern.sub('', content)
        
        # Remove multiple consecutive blank lines (max 2)
        cleaned = re.sub(r'\n\n\n+', '\n\n', cleaned)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(cleaned)
        
        print(f"✓ Cleaned {filepath}")

print("\nDone!")
