# tests/test_google_oauth.py
import os
import time
import pytest
import jwt as pyjwt

# Env vars already set by conftest.py

from utils.google_oauth import (
    generate_oauth_state,
    verify_oauth_state,
)

def test_generate_oauth_state_is_valid_jwt():
    state = generate_oauth_state()
    payload = pyjwt.decode(
        state,
        os.environ['JWT_SECRET'],
        algorithms=['HS256'],
    )
    assert 'nonce' in payload
    assert len(payload['nonce']) > 8

def test_generate_oauth_state_has_short_expiry():
    state = generate_oauth_state()
    payload = pyjwt.decode(
        state,
        os.environ['JWT_SECRET'],
        algorithms=['HS256'],
    )
    ttl = payload['exp'] - payload['iat']
    assert ttl == 300  # 5 minutes

def test_verify_oauth_state_accepts_valid_state():
    state = generate_oauth_state()
    assert verify_oauth_state(state) is True

def test_verify_oauth_state_rejects_expired_state():
    payload = {
        'nonce': 'abc123',
        'iat': int(time.time()) - 400,
        'exp': int(time.time()) - 100,
    }
    expired = pyjwt.encode(payload, os.environ['JWT_SECRET'], algorithm='HS256')
    assert verify_oauth_state(expired) is False

def test_verify_oauth_state_rejects_wrong_signature():
    payload = {
        'nonce': 'abc123',
        'iat': int(time.time()),
        'exp': int(time.time()) + 300,
    }
    bad_state = pyjwt.encode(payload, 'wrong-secret', algorithm='HS256')
    assert verify_oauth_state(bad_state) is False

def test_verify_oauth_state_rejects_empty_string():
    assert verify_oauth_state('') is False

def test_verify_oauth_state_rejects_garbage():
    assert verify_oauth_state('not.a.jwt') is False
