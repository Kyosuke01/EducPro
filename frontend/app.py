import os
import requests
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SESSION_SECRET_KEY", "educpro_secret_key_2026")
app.permanent_session_lifetime = timedelta(minutes=30)
API_URL = "http://backend:5000"
API_SECRET_KEY = os.getenv("API_SECRET_KEY", "")
USER_AGENT = "educrpro/1.0"
TWO_FACTOR_TEMPLATE = "two_factor.html"


def get_secure_headers():
    return {
        "X-API-Key": API_SECRET_KEY,
        "User-Agent": USER_AGENT,
        "Content-Type": "application/json"
    }


def persist_user_session(user: dict):
    session.permanent = True
    session["user_id"] = user.get("id")
    session["first_name"] = user.get("first_name")
    session["last_name"] = user.get("last_name")
    session["email"] = user.get("email")
    session["role"] = user.get("role")
    session["class_name"] = user.get("class_name")
    session["topic_name"] = user.get("topic_name")
    session["has_2fa"] = user.get("has_2fa", False)
    session["ip"] = request.remote_addr
    session["user_agent"] = request.headers.get("User-Agent")


def clear_pending_2fa():
    session.pop("pending_2fa_token", None)
    session.pop("pending_user_preview", None)


def start_pending_2fa(token, user_preview=None):
    session["pending_2fa_token"] = token
    session["pending_user_preview"] = user_preview or {}

# Page de connexion


@app.route("/", methods=["GET"])
def index():
    error = request.args.get("error")
    return render_template("index.html", error=error)

# POST /login — Proxy vers le backend


@app.route("/login", methods=["POST"])
def login():
    clear_pending_2fa()
    email = request.form.get("email")
    password = request.form.get("password")

    if not email or not password:
        return redirect(url_for("index", error="Veuillez remplir tous les champs."))

    try:
        payload = {"email": email, "password": password}
        resp = requests.post(f"{API_URL}/api/auth/login", headers=get_secure_headers(), json=payload, timeout=5)

        if resp.status_code == 200:
            data = resp.json()
            user = data.get("user", {})
            persist_user_session(user)
            return redirect(url_for("dashboard"))
        elif resp.status_code == 202:
            data = resp.json()
            token = data.get("pending_token")
            if token:
                start_pending_2fa(token, data.get("user"))
                return redirect(url_for("two_factor"))
            error_msg = data.get("error", "Code A2F requis.")
            return redirect(url_for("index", error=error_msg))
        else:
            error_msg = resp.json().get("error", "Identifiants incorrects.")
            return redirect(url_for("index", error=error_msg))

    except requests.exceptions.RequestException:
        return redirect(url_for("index", error="Impossible de contacter le serveur. Réessayez."))


@app.route("/verify-2fa", methods=["GET", "POST"])
def two_factor():
    pending_token = session.get("pending_2fa_token")
    pending_user = session.get("pending_user_preview", {})

    if not pending_token:
        clear_pending_2fa()
        return redirect(url_for("index", error="La vérification A2F a expiré. Veuillez vous reconnecter."))

    if request.method == "GET":
        return render_template(TWO_FACTOR_TEMPLATE, user=pending_user, error=None)

    code = (request.form.get("code") or "").strip()
    if len(code) != 6 or not code.isdigit():
        return render_template(TWO_FACTOR_TEMPLATE, user=pending_user, error="Veuillez saisir un code à 6 chiffres.")

    try:
        payload = {"token": pending_token, "code": code}
        resp = requests.post(f"{API_URL}/api/auth/login/2fa", headers=get_secure_headers(), json=payload, timeout=5)

        if resp.status_code == 200:
            data = resp.json()
            user = data.get("user", {})
            persist_user_session(user)
            clear_pending_2fa()
            return redirect(url_for("dashboard"))
        else:
            error_msg = resp.json().get("error", "Code A2F invalide.")
            return render_template(TWO_FACTOR_TEMPLATE, user=pending_user, error=error_msg)
    except requests.exceptions.RequestException:
        return render_template(TWO_FACTOR_TEMPLATE, user=pending_user, error="Impossible de contacter le serveur. Réessayez.")

# Dashboard — protégé par session


@app.route("/dashboard", methods=["GET"])
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
                           topic_name=session.get("topic_name"),
                           has_2fa=session.get("has_2fa", False)
                           )

# Logout

# Synchronisation de session — 2FA


@app.route("/session/sync-2fa", methods=["POST"])
def sync_2fa_session():
    """Met à jour l'état has_2fa dans la session Flask après activation/désactivation."""
    if "user_id" not in session:
        return jsonify({"error": "Non authentifié"}), 401
    data = request.get_json(silent=True) or {}
    # Le frontend envoie {"has_2fa": true/false}
    session["has_2fa"] = bool(data.get("has_2fa", False))
    return jsonify({"ok": True, "has_2fa": session["has_2fa"]}), 200


@app.route("/logout", methods=["GET"])
def logout():
    session.clear()
    return redirect(url_for("index"))


def _check_rbac_permission(method, path, role):
    """Check if user has permission to execute this method on this resource."""
    public_routes = ["auth/forgot-password", "auth/reset-password"]

    if method not in ["POST", "PUT", "DELETE"] or path in public_routes:
        return True, None  # No RBAC restrictions

    first_segment = path.split("/")[0] if path else ""

    if role == "student":
        allowed = ["messages", "auth", "users"]
        if first_segment not in allowed:
            return False, jsonify({"error": "Action refusée. Accès administrateur requis."}), 403

    elif role == "teacher":
        allowed = ["attendance", "grades", "messages", "edt", "auth", "users"]
        if first_segment not in allowed:
            return False, jsonify({"error": "Action non autorisée pour un enseignant."}), 403

    return True, None, None


def _make_api_request(method, url, headers):
    """Centralized API request maker."""
    timeout = 10
    if method == "GET":
        return requests.get(url, headers=headers, params=request.args, timeout=timeout)
    elif method == "POST":
        return requests.post(url, headers=headers, json=request.get_json(), timeout=timeout)
    elif method == "PUT":
        return requests.put(url, headers=headers, json=request.get_json(), timeout=timeout)
    elif method == "DELETE":
        return requests.delete(url, headers=headers, timeout=timeout)
    else:
        raise ValueError(f"Unsupported method: {method}")

# API Proxy — redirige les appels vers le backend


@app.route("/api/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
def api_proxy(path):
    public_routes = ["auth/forgot-password", "auth/reset-password"]

    if path not in public_routes and "user_id" not in session:
        return jsonify({"error": "Non authentifié"}), 401

    # Check RBAC permission
    role = session.get("role")
    method = request.method
    is_allowed, error_response, error_code = _check_rbac_permission(method, path, role)
    if not is_allowed:
        return error_response, error_code

    url = f"{API_URL}/api/{path}"
    headers = get_secure_headers()

    try:
        resp = _make_api_request(method, url, headers)

        # Log minimal proxy info pour diagnostiquer les retours inattendus
        app.logger.info(f"[proxy] {request.method} /api/{path} -> {resp.status_code} {resp.headers.get('Content-Type')}")

        # Propager le Content-Type réel pour éviter de forcer du JSON sur des réponses 404/HTML
        content_type = resp.headers.get("Content-Type", "application/json")
        return (resp.content, resp.status_code, {"Content-Type": content_type})

    except requests.exceptions.RequestException as e:
        app.logger.error(f"[proxy] backend exception {e}")
        return jsonify({"error": f"Erreur de communication avec le backend : {str(e)}"}), 502

# Pages Légales


@app.route("/legal", methods=["GET"])
def legal():
    """Page des Mentions Légales"""
    return render_template("legal.html")


@app.route("/privacy", methods=["GET"])
def privacy():
    """Page de la Politique de Confidentialité"""
    return render_template("privacy.html")


if __name__ == "__main__":
    host = os.getenv("FRONTEND_HOST", "0.0.0.0")
    debug_mode = os.getenv("DEBUG", "False").lower() == "true"
    app.run(host=host, port=3000, debug=debug_mode)
