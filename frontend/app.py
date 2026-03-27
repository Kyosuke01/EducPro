import requests
from flask import Flask, render_template

app = Flask(__name__)
API_URL = "http://backend:5000"

@app.route("/")
def index():
    try:
        users = requests.get(f"{API_URL}/api/users/").json()
    except:
        users = []
    return render_template("index.html", users=users)

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)