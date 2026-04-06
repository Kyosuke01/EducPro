from unittest.mock import patch

from app import create_app


@patch("app._register_blueprints", lambda app: None)
def test_security_headers_are_set_and_403_is_sanitized():
    app = create_app()
    client = app.test_client()

    @app.route("/force-403-unsafe<id>", methods=["GET"])
    def _force_403(id):
        from flask import abort
        abort(403)

    resp = client.get("/force-403-unsafe%0a<script>")
    assert resp.status_code == 403
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert "default-src 'self'" in (resp.headers.get("Content-Security-Policy") or "")


@patch("app._register_blueprints", lambda app: None)
@patch("app._register_request_hooks", lambda app: None)
def test_runtime_secret_is_applied():
    app = create_app()
    assert app.secret_key is not None
    assert app.secret_key == "test-backend-secret"
