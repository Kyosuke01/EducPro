import requests
from flask import Flask, render_template

app = Flask(__name__)
API_URL = "http://backend:5000"

@app.route("/")
def index():
    users = requests.get(f"{API_URL}/api/users/").json()
    return render_template("index.html", users=users)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)