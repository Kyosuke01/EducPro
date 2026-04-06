from unittest.mock import patch

from app import _validate_api_request, create_app


def _test_env_getter(key):
    mapping = {
        "DB_USER": "test",
        "DB_PASSWORD": "test",
        "DB_HOST": "localhost",
        "DB_PORT": "3306",
        "DB_NAME": "testdb",
        "API_SECRET_KEY": "test-api-key",
        "BACKEND_SECRET_KEY": "test-backend-secret",
        "FLASK_ENV": "test",
        "ENVIRONMENT": "test",
    }
    return mapping.get(key)


def test_validate_api_request_rejects_bad_user_agent(app_ctx):
    app = create_app()
    with app.test_request_context("/api/ping", headers={"User-Agent": "x", "X-API-Key": "x"}):
        with patch("app._check_user_agent", return_value=(False, "UA_ERR", 403)):
            resp, code = _validate_api_request(lambda: (True, None))
    assert resp == "UA_ERR"
    assert code == 403


def test_validate_api_request_rejects_bad_api_key(app_ctx):
    app = create_app()
    with app.test_request_context("/api/ping", headers={"User-Agent": "x", "X-API-Key": "x"}):
        with patch("app._check_user_agent", return_value=(True, None, None)), \
             patch("app._check_api_key", return_value=(False, "KEY_ERR", 401)):
            resp, code = _validate_api_request(lambda: (True, None))
    assert resp == "KEY_ERR"
    assert code == 401


def test_validate_api_request_rejects_bad_session(app_ctx):
    app = create_app()
    with app.test_request_context("/api/ping", headers={"User-Agent": "x", "X-API-Key": "x"}):
        with patch("app._check_user_agent", return_value=(True, None, None)), \
             patch("app._check_api_key", return_value=(True, None, None)):
            resp, code = _validate_api_request(lambda: (False, "SESSION_ERR"))
    assert resp == "SESSION_ERR"
    assert code == 403


def test_validate_api_request_ok(app_ctx):
    app = create_app()
    with app.test_request_context("/api/ping", headers={"User-Agent": "x", "X-API-Key": "x"}):
        with patch("app._check_user_agent", return_value=(True, None, None)), \
             patch("app._check_api_key", return_value=(True, None, None)):
            resp, code = _validate_api_request(lambda: (True, None))
    assert resp is None
    assert code is None


@patch("app._register_blueprints", lambda app: None)
@patch("app.os.getenv", side_effect=lambda key: "production" if key == "ENVIRONMENT" else _test_env_getter(key))
def test_hsts_header_enabled_in_production(_mock_getenv):
    app = create_app()

    @app.route("/ok-hsts", methods=["GET"])
    def _ok_hsts():
        return {"ok": True}, 200

    client = app.test_client()
    resp = client.get("/ok-hsts")
    assert resp.status_code == 200
    assert resp.headers.get("Strict-Transport-Security") == "max-age=31536000; includeSubDomains"
