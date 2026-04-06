import os
import pytest


def pytest_sessionstart(session):
    os.environ.setdefault("DB_USER", "test")
    os.environ.setdefault("DB_PASSWORD", "test")
    os.environ.setdefault("DB_HOST", "localhost")
    os.environ.setdefault("DB_PORT", "3306")
    os.environ.setdefault("DB_NAME", "testdb")
    os.environ.setdefault("API_SECRET_KEY", "test-api-key")
    os.environ.setdefault("BACKEND_SECRET_KEY", "test-backend-secret")
    os.environ.setdefault("FLASK_ENV", "test")
    os.environ.setdefault("ENVIRONMENT", "test")


@pytest.fixture
def app_ctx():
    from app import create_app
    app = create_app()
    with app.app_context():
        yield
