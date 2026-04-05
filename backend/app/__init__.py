from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv
import os
import secrets
import sys

load_dotenv()
db = SQLAlchemy()


def _ensure_secret_key():
    """
    SECURITY: Ensure SECRET_KEY is properly configured from environment.
    For production: SECRET_KEY MUST be set via environment variables (from cloud provider).
    For development: If missing, generate once and save to .env file.
    This avoids hard-coded credentials (S2068) by ensuring all values come from env.
    """
    # Check if SECRET_KEY already exists in environment
    if os.getenv("BACKEND_SECRET_KEY") or os.getenv("API_SECRET_KEY"):
        return  # Already configured

    # Production: fail immediately if SECRET_KEY is not set
    if os.getenv("FLASK_ENV") == "production" or os.getenv("ENVIRONMENT") == "production":
        print("CRITICAL ERROR: SECRET_KEY is not configured!", file=sys.stderr)
        print("Set BACKEND_SECRET_KEY or API_SECRET_KEY environment variable", file=sys.stderr)
        sys.exit(1)

    # Development only: Generate key and save to .env if not present
    env_file = ".env"
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            env_content = f.read()
            if "BACKEND_SECRET_KEY=" in env_content:
                return  # Already in .env, just reload

    # Generate new key and append to .env
    new_key = secrets.token_hex(32)
    with open(env_file, 'a') as f:
        f.write("\n# Auto-generated for development (change for production)\n")
        f.write(f"BACKEND_SECRET_KEY={new_key}\n")

    # Reload environment variables
    load_dotenv()
    print("⚠️  Generated and saved BACKEND_SECRET_KEY to .env (development only)", file=sys.stderr)


def create_app():
    # Ensure SECRET_KEY is properly configured from environment
    _ensure_secret_key()

    app = Flask(__name__)
    CORS(app)
    app.json.ensure_ascii = False

    # SECURITY: Secret key ALWAYS from environment variables (S2068 - no hard-coded credentials)
    secret_key = os.getenv("BACKEND_SECRET_KEY") or os.getenv("API_SECRET_KEY")

    # At this point, secret_key is guaranteed to exist and come from environment
    app.config["SECRET_KEY"] = secret_key

    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}?charset=utf8mb4"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    from app.routes.users import users_bp
    from app.routes.auth import auth_bp
    from app.routes.classes import classes_bp
    from app.routes.attendance import attendance_bp
    from app.routes.edt import edt_bp
    from app.routes.grades import grades_bp
    from app.routes.messages import messages_bp

    app.register_blueprint(users_bp, url_prefix="/api/users")
    app.register_blueprint(auth_bp, url_prefix="/api")
    app.register_blueprint(classes_bp, url_prefix="/api")
    app.register_blueprint(attendance_bp, url_prefix="/api")
    app.register_blueprint(edt_bp, url_prefix="/api")
    app.register_blueprint(grades_bp, url_prefix="/api")
    app.register_blueprint(messages_bp, url_prefix="/api")

    # Import inside create_app for route-specific dependencies
    from flask import request, jsonify, render_template
    from app.rbac import validate_session_security

    def _check_user_agent(user_agent):
        """Validate User-Agent header."""
        valid_agents = ["educrpro/1.0", "educpro-admin/1.0"]
        if user_agent not in valid_agents:
            return False, jsonify({"error": "Forbidden: Invalid User-Agent"}), 403
        return True, None, None

    def _check_api_key(provided_key):
        """Validate API key header."""
        secret_key = os.getenv("API_SECRET_KEY")
        if provided_key != secret_key:
            return False, jsonify({"error": "Unauthorized: Invalid API Key"}), 401
        return True, None, None

    def _validate_api_request():
        """Validate API request (User-Agent + API Key + Session)."""
        # Check User-Agent
        user_agent = request.headers.get("User-Agent")
        is_valid_ua, ua_response, ua_code = _check_user_agent(user_agent)
        if not is_valid_ua:
            return ua_response, ua_code

        # Check API Key
        api_key = request.headers.get("X-API-Key")
        is_valid_key, key_response, key_code = _check_api_key(api_key)
        if not is_valid_key:
            return key_response, key_code

        # Validate session security
        is_valid_session, session_response = validate_session_security()
        if not is_valid_session:
            return session_response, 403

        return None, None

    @app.before_request
    def require_api_key_and_ua():
        """Protect API endpoints with User-Agent, API Key, and session validation."""
        if request.path.startswith("/api/"):
            error_response, error_code = _validate_api_request()
            if error_response is not None:
                return error_response, error_code

    @app.after_request
    def set_security_headers(response):
        """
        SECURITY: Ajoute les en-têtes de sécurité HTTP pour prévenir:
        - XSS (Content-Security-Policy)
        - Clickjacking (X-Frame-Options)
        - MIME sniffing (X-Content-Type-Options)
        - SSL/TLS enforcement (Strict-Transport-Security)
        """
        # Prévention du XSS avec CSP (Content-Security-Policy)
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' cdn.jsdelivr.net unpkg.com; "
            "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net fonts.googleapis.com; "
            "font-src 'self' fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )

        # Prévention du clickjacking
        response.headers['X-Frame-Options'] = 'DENY'

        # Prévention du MIME type sniffing (XSS via fichiers)
        response.headers['X-Content-Type-Options'] = 'nosniff'

        # Protection XSS du navigateur (legacy)
        response.headers['X-XSS-Protection'] = '1; mode=block'

        # Force HTTPS en production
        if os.getenv("ENVIRONMENT") == "production":
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        # Désactiver le referrer policy pour éviter les fuites d'info
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        return response

    @app.route("/health")
    def health():
        return {"status": "ok"}, 200

    # Error handler pour 403 Forbidden
    @app.errorhandler(403)
    def forbidden(error):
        """Gère les erreurs 403 avec une belle page**"""
        if request.path.startswith("/api/"):
            return jsonify({
                "error": "Forbidden",
                "message": "Vous n'avez pas les permissions pour accéder à cette ressource.",
                "status": 403
            }), 403
        try:
            return render_template("403.html"), 403
        except Exception:
            return "403 - Forbidden", 403

    return app
