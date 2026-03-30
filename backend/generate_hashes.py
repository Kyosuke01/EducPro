import sys
import subprocess

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

try:
    import bcrypt
except ImportError:
    install('bcrypt')
    import bcrypt

h1 = bcrypt.hashpw(b'admin123', bcrypt.gensalt(14)).decode()
h2 = bcrypt.hashpw(b'prof123', bcrypt.gensalt(14)).decode()
h3 = bcrypt.hashpw(b'eleve123', bcrypt.gensalt(14)).decode()

print(f"ADMIN: {h1}")
print(f"PROF: {h2}")
print(f"ELEVE: {h3}")
