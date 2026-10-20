import base64
import email
import importlib
from unittest.mock import MagicMock

import pytest

from utils.email import create_message
from utils.queries import is_valid_email
from utils.data_sanitizer import sanitize_email


@pytest.fixture
def config_env():
    """Yield a MonkeyPatch plus a reloader; env is restored before the final reload."""
    import utils.config as cfg
    with pytest.MonkeyPatch.context() as mp:
        yield mp, lambda: importlib.reload(cfg)
    importlib.reload(cfg)


def test_bypass_group_check_ignored_in_production(config_env):
    monkeypatch, reload_config = config_env
    monkeypatch.setenv('BYPASS_GROUP_CHECK', 'true')
    monkeypatch.setenv('STREAMLIT_ENV', 'production')
    assert reload_config().BYPASS_GROUP_CHECK is False


def test_bypass_group_check_ignored_when_env_unset(config_env):
    monkeypatch, reload_config = config_env
    monkeypatch.setenv('BYPASS_GROUP_CHECK', 'true')
    monkeypatch.delenv('STREAMLIT_ENV', raising=False)
    assert reload_config().BYPASS_GROUP_CHECK is False


def test_bypass_group_check_honoured_in_development(config_env):
    monkeypatch, reload_config = config_env
    monkeypatch.setenv('BYPASS_GROUP_CHECK', 'true')
    monkeypatch.setenv('STREAMLIT_ENV', 'development')
    assert reload_config().BYPASS_GROUP_CHECK is True


@pytest.mark.parametrize('value', [
    'user@westkingdom.org\n',
    'user@westkingdom.org\nbcc: victim@example.com',
    'user@westkingdom.org.evil.com',
])
def test_is_valid_email_rejects_trailing_content(value):
    assert is_valid_email(value) is False


def test_sanitize_email_rejects_embedded_newline():
    with pytest.raises(ValueError):
        sanitize_email('user@example.com\nfoo')


def test_create_message_strips_header_injection():
    msg = create_message(
        'sender@westkingdom.org',
        'to@westkingdom.org',
        '',
        'Hello\r\nBcc: victim@example.com',
        'body',
    )
    parsed = email.message_from_bytes(base64.urlsafe_b64decode(msg['raw']))
    assert parsed['Bcc'] is None
    assert '\n' not in parsed['Subject']


def test_api_quotes_path_segments():
    from utils.api import RegnumAPI

    api = RegnumAPI(base_url='http://api.test')
    api.session = MagicMock()
    api.remove_member_from_group('abc/../admin', 'a@westkingdom.org?x=1')
    url = api.session.delete.call_args[0][0]
    assert url == 'http://api.test/groups/abc%2F..%2Fadmin/members/a@westkingdom.org%3Fx%3D1'
