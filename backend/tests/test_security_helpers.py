from unittest.mock import patch

from app import _check_api_key, _check_user_agent


def test_check_user_agent_accepts_known_agent(app_ctx):
    ok, resp, code = _check_user_agent("educrpro/1.0")
    assert ok is True
    assert resp is None
    assert code is None


def test_check_user_agent_rejects_unknown_agent(app_ctx):
    ok, resp, code = _check_user_agent("bad-agent")
    assert ok is False
    assert code == 403
    assert resp.get_json()["error"] == "Forbidden: Invalid User-Agent"


@patch("app.os.getenv", return_value="good-key")
def test_check_api_key_accepts_expected(mock_getenv, app_ctx):
    ok, resp, code = _check_api_key("good-key")
    assert ok is True
    assert resp is None
    assert code is None


@patch("app.os.getenv", return_value="good-key")
def test_check_api_key_rejects_wrong(mock_getenv, app_ctx):
    ok, resp, code = _check_api_key("bad-key")
    assert ok is False
    assert code == 401
    assert resp.get_json()["error"] == "Unauthorized: Invalid API Key"
