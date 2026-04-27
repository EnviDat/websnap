"""Tests for src/websnap/session.py"""

import requests
from requests.adapters import HTTPAdapter

from websnap.session import make_session


def test_make_session_returns_session():
    assert isinstance(make_session(), requests.Session)


def test_make_session_mounts_https():
    session = make_session()
    adapter = session.get_adapter("https://example.com")
    assert isinstance(adapter, HTTPAdapter)


def test_make_session_mounts_http():
    session = make_session()
    adapter = session.get_adapter("http://example.com")
    assert isinstance(adapter, HTTPAdapter)


def test_make_session_retry_config():
    session = make_session()
    adapter = session.get_adapter("https://example.com")
    assert isinstance(adapter, HTTPAdapter)
    retry = adapter.max_retries
    assert retry.total == 3
    assert retry.backoff_factor == 1
    assert set(retry.status_forcelist) == {429, 500, 502, 503, 504}
