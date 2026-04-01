from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv
import os

load_dotenv()
db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    CORS(app)
    app.json.ensure_ascii = False
    app.config["SECRET_KEY"] = os.getenv("BACKEND_SECRET_KEY", os.getenv("API_SECRET_KEY", "educpro-backend-secret"))

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

    from flask import request, jsonify

    @app.before_request
    def require_api_key_and_ua():
        # On ne protège que les routes qui matchent /api/ (sauf exceptions si nécessaire)
        if request.path.startswith("/api/"):
            # Vérification du User-Agent
            user_agent = request.headers.get("User-Agent")
            if user_agent not in ["educrpro/1.0", "educpro-admin/1.0"]:
                return jsonify({"error": "Forbidden: Invalid User-Agent"}), 403

            # Vérification de la clé API
            secret_key = os.getenv("API_SECRET_KEY")
            if request.headers.get("X-API-Key") != secret_key:
                return jsonify({"error": "Unauthorized: Invalid API Key"}), 401

    @app.route("/health")
    def health():
        return {"status": "ok"}, 200

    return app
