import os
import requests
from flask import Flask, render_template

app = Flask(__name__)
API_URL = "http://backend:5000"
API_SECRET_KEY = os.getenv("API_SECRET_KEY", "eDucPRo_s3cr3t_ApI_k3y_2026!")

@app.route("/")
def dashboard():
    headers = {
        "X-API-Key": API_SECRET_KEY,
        "User-Agent": "educrpro/1.0"
    }
    users = requests.get(f"{API_URL}/api/users/", headers=headers).json()
    return render_template("dashboard.html", users=users)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3001, debug=True)