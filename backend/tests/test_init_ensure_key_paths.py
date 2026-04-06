from pathlib import Path
from unittest.mock import patch

import app


def test_ensure_secret_key_returns_when_present():
    with patch('app.os.getenv', side_effect=lambda k: 'x' if k in {'BACKEND_SECRET_KEY', 'API_SECRET_KEY'} else None):
        app._ensure_secret_key()


def test_ensure_secret_key_generates_in_dev(tmp_path):
    env_file = tmp_path / '.env'

    def fake_getenv(key):
        if key in {'BACKEND_SECRET_KEY', 'API_SECRET_KEY', 'FLASK_ENV', 'ENVIRONMENT'}:
            return None
        return None

    with patch('app.os.getenv', side_effect=fake_getenv), \
         patch('app.os.path.exists', return_value=False), \
         patch('app.open', create=True) as mocked_open, \
         patch('app.load_dotenv'):
        app._ensure_secret_key()
        assert mocked_open.called


def test_ensure_secret_key_exits_in_production_without_key():
    def fake_getenv(key):
        if key in {'BACKEND_SECRET_KEY', 'API_SECRET_KEY'}:
            return None
        if key == 'FLASK_ENV':
            return 'production'
        return None

    with patch('app.os.getenv', side_effect=fake_getenv), patch('app.sys.exit', side_effect=SystemExit):
        try:
            app._ensure_secret_key()
        except SystemExit:
            pass
        else:
            raise AssertionError('SystemExit expected')
