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

    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    from app.models.user import User
    from app.models.course import Course
    from app.models.lesson import Lesson

    from app.routes.users import users_bp
    from app.routes.auth import auth_bp
    from app.routes.classes import classes_bp
    from app.routes.attendance import attendance_bp
    from app.routes.edt import edt_bp
    from app.routes.grades import grades_bp

    app.register_blueprint(users_bp, url_prefix="/api/users")
    app.register_blueprint(auth_bp, url_prefix="/api")
    app.register_blueprint(classes_bp, url_prefix="/api")
    app.register_blueprint(attendance_bp, url_prefix="/api")
    app.register_blueprint(edt_bp, url_prefix="/api")
    app.register_blueprint(grades_bp, url_prefix="/api")

    @app.route("/health")
    def health():
        return {"status": "ok"}, 200

    return app