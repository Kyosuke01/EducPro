from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv
import os
import secrets
import sys
import re

load_dotenv()
sqlalchemy_db = SQLAlchemy()
db = sqlalchemy_db


def _ensure_secret_key():
    """
    SECURITY: Ensure secret key is properly configured from environment.
    For production: key MUST be set via environment variables.
    For development: if missing, generate once and save to .env file.
    """
    if os.getenv("BACKEND_SECRET_KEY") or os.getenv("API_SECRET_KEY"):
        return

    if os.getenv("FLASK_ENV") == "production" or os.getenv("ENVIRONMENT") == "production":
        print("CRITICAL ERROR: backend key is not configured!", file=sys.stderr)
        print("Set BACKEND_SECRET_KEY or API_SECRET_KEY environment variable", file=sys.stderr)
        sys.exit(1)

    env_file = ".env"
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            if "BACKEND_SECRET_KEY=" in f.read():
                return

    new_key = secrets.token_hex(32)
    with open(env_file, "a") as f:
        f.write("\n# Auto-generated for development (change for production)\n")
        f.write(f"BACKEND_SECRET_KEY={new_key}\n")

    load_dotenv()
    print("Generated and saved BACKEND_SECRET_KEY to .env (development only)", file=sys.stderr)


def _get_runtime_secret():
    return os.getenv("BACKEND_SECRET_KEY") or os.getenv("API_SECRET_KEY")


def _register_blueprints(app):
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


def _check_user_agent(user_agent):
    valid_agents = ["educrpro/1.0", "educpro-admin/1.0"]
    if user_agent not in valid_agents:
        return False, jsonify({"error": "Forbidden: Invalid User-Agent"}), 403
    return True, None, None


def _check_api_key(provided_key):
    expected_api_key = os.getenv("API_SECRET_KEY")
    if provided_key != expected_api_key:
        return False, jsonify({"error": "Unauthorized: Invalid API Key"}), 401
    return True, None, None


def _validate_api_request(validate_session_security):
    user_agent = request.headers.get("User-Agent")
    is_valid_ua, ua_response, ua_code = _check_user_agent(user_agent)
    if not is_valid_ua:
        return ua_response, ua_code

    api_key = request.headers.get("X-API-Key")
    is_valid_key, key_response, key_code = _check_api_key(api_key)
    if not is_valid_key:
        return key_response, key_code

    is_valid_session, session_response = validate_session_security()
    if not is_valid_session:
        return session_response, 403

    return None, None


def _register_request_hooks(app):
    from app.rbac import validate_session_security

    def _sanitize_log_value(value, max_len=120):
        text = str(value) if value is not None else "UNKNOWN"
        safe = re.sub(r"[^a-zA-Z0-9._/@:-]", "", text)
        return safe[:max_len] or "UNKNOWN"

    @app.before_request
    def require_api_key_and_ua():
        if request.path.startswith("/api/"):
            error_response, error_code = _validate_api_request(validate_session_security)
            if error_response is not None:
                return error_response, error_code

    @app.after_request
    def set_security_headers(response):
        response.headers["Content-Security-Policy"] = (
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
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        if os.getenv("ENVIRONMENT") == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        if response.status_code == 403:
            app.logger.warning(
                "403 FORBIDDEN | method=%s | path=%s | ip=%s | ua=%s",
                _sanitize_log_value(request.method, 16),
                _sanitize_log_value(request.path, 200),
                _sanitize_log_value(request.remote_addr, 45),
                _sanitize_log_value(request.headers.get("User-Agent", "UNKNOWN"), 120)
            )

        return response


def _register_routes_and_errors(app):
    @app.route("/health", methods=["GET"])
    def health():
        return {"status": "ok"}, 200

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            "error": "Forbidden",
            "message": "Vous n'avez pas les permissions pour accéder à cette ressource.",
            "status": 403
        }), 403

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "error": "Not Found",
            "message": "La ressource demandée est introuvable.",
            "status": 404
        }), 404


def create_app():
    _ensure_secret_key()

    app = Flask(__name__)
    CORS(app)
    app.json.ensure_ascii = False

    runtime_secret = _get_runtime_secret()
    app.secret_key = runtime_secret

    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}?charset=utf8mb4"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    sqlalchemy_db.init_app(app)
    _register_blueprints(app)
    _register_request_hooks(app)
    _register_routes_and_errors(app)

    return app
