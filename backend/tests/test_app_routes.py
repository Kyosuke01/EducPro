from unittest.mock import patch

from app import create_app


@patch("app._register_blueprints", lambda app: None)
@patch("app._register_request_hooks", lambda app: None)
def test_health_route_returns_ok():
    app = create_app()
    client = app.test_client()

    resp = client.get("/health")

    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


@patch("app._register_blueprints", lambda app: None)
@patch("app._register_request_hooks", lambda app: None)
def test_error_handlers_return_json():
    app = create_app()

    @app.route("/force-403", methods=["GET"])
    def _force_403():
        from flask import abort
        abort(403)

    client = app.test_client()

    resp_404 = client.get("/definitely-not-found")
    assert resp_404.status_code == 404
    body_404 = resp_404.get_json()
    assert body_404["error"] == "Not Found"

    resp_403 = client.get("/force-403")
    assert resp_403.status_code == 403
    body_403 = resp_403.get_json()
    assert body_403["error"] == "Forbidden"
