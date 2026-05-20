import os
import importlib
import pytest

def test_config_raises_when_client_id_missing(monkeypatch):
    monkeypatch.delenv('GOOGLE_CLIENT_ID', raising=False)
    monkeypatch.setenv('JWT_SECRET', 'test-secret')
    monkeypatch.setenv('GOOGLE_CLIENT_SECRET', 'test-secret')
    with pytest.raises(RuntimeError, match='GOOGLE_CLIENT_ID'):
        import utils.config as cfg
        importlib.reload(cfg)

def test_config_raises_when_client_secret_missing(monkeypatch):
    monkeypatch.delenv('GOOGLE_CLIENT_SECRET', raising=False)
    monkeypatch.setenv('JWT_SECRET', 'test-secret')
    monkeypatch.setenv('GOOGLE_CLIENT_ID', 'test-client-id')
    with pytest.raises(RuntimeError, match='GOOGLE_CLIENT_SECRET'):
        import utils.config as cfg
        importlib.reload(cfg)
