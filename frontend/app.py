import os
import requests
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = "educpro_secret_key_2026"
app.permanent_session_lifetime = timedelta(minutes=30)
API_URL = "http://backend:5000"
API_SECRET_KEY = os.getenv("API_SECRET_KEY", "")
USER_AGENT = "educrpro/1.0"

def get_secure_headers():
    return {
        "X-API-Key": API_SECRET_KEY,
        "User-Agent": USER_AGENT,
        "Content-Type": "application/json"
    }


# ──────────────────────────────────────────────
# Page de connexion
# ──────────────────────────────────────────────
@app.route("/")
def index():
    error = request.args.get("error")
    return render_template("index.html", error=error)


# ──────────────────────────────────────────────
# POST /login — Proxy vers le backend
# ──────────────────────────────────────────────
@app.route("/login", methods=["POST"])
def login():
    email = request.form.get("email")
    password = request.form.get("password")

    if not email or not password:
        return redirect(url_for("index", error="Veuillez remplir tous les champs."))

    try:
        resp = requests.post(f"{API_URL}/api/auth/login", headers=get_secure_headers(), json={
            "email": email,
            "password": password
        }, timeout=5)

        if resp.status_code == 200:
            data = resp.json()
            user = data.get("user", {})
            session.permanent = True
            session["user_id"] = user.get("id")
            session["first_name"] = user.get("first_name")
            session["last_name"] = user.get("last_name")
            session["email"] = user.get("email")
            session["role"] = user.get("role")
            session["class_name"] = user.get("class_name")
            session["topic_name"] = user.get("topic_name")
            
            # Anti-hijacking
            session["ip"] = request.remote_addr
            session["user_agent"] = request.headers.get("User-Agent")
            
            return redirect(url_for("dashboard"))
        else:
            error_msg = resp.json().get("error", "Identifiants incorrects.")
            return redirect(url_for("index", error=error_msg))

    except requests.exceptions.RequestException:
        return redirect(url_for("index", error="Impossible de contacter le serveur. Réessayez."))


# ──────────────────────────────────────────────
# Dashboard — protégé par session
# ──────────────────────────────────────────────
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("index", error="Veuillez vous connecter."))
        
    if session.get("ip") != request.remote_addr or session.get("user_agent") != request.headers.get("User-Agent"):
        session.clear()
        return redirect(url_for("index", error="Session invalide. Veuillez vous reconnecter."))

    return render_template("dashboard.html",
        user_id=session.get("user_id"),
        first_name=session.get("first_name"),
        last_name=session.get("last_name"),
        email=session.get("email"),
        role=session.get("role"),
        class_name=session.get("class_name"),
        topic_name=session.get("topic_name")
    )


# ──────────────────────────────────────────────
# Logout
# ──────────────────────────────────────────────
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# ──────────────────────────────────────────────
# API Proxy — redirige les appels vers le backend
# ──────────────────────────────────────────────
@app.route("/api/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
def api_proxy(path):
    if "user_id" not in session:
        return jsonify({"error": "Non authentifié"}), 401

    url = f"{API_URL}/api/{path}"
    headers = get_secure_headers()

    try:
        if request.method == "GET":
            resp = requests.get(url, headers=headers, params=request.args, timeout=10)
        elif request.method == "POST":
            resp = requests.post(url, headers=headers, json=request.get_json(), timeout=10)
        elif request.method == "PUT":
            resp = requests.put(url, headers=headers, json=request.get_json(), timeout=10)
        elif request.method == "DELETE":
            resp = requests.delete(url, headers=headers, timeout=10)
        else:
            return jsonify({"error": "Méthode non supportée"}), 405

        return (resp.content, resp.status_code, {"Content-Type": "application/json"})

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Erreur de communication avec le backend : {str(e)}"}), 502


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)