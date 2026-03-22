import time
import pytest
import responses
from unittest.mock import patch, MagicMock

from nse.client import NSESession, BASE_URL, SESSION_TTL


@responses.activate
def test_refresh_on_init():
    responses.add(responses.GET, BASE_URL, body="OK", status=200)

    with patch("nse.client.time.sleep"):
        session = NSESession()

    assert session._last_refresh > 0
    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == BASE_URL + "/"


@responses.activate
def test_session_refresh_after_ttl():
    responses.add(responses.GET, BASE_URL, body="OK", status=200)
    responses.add(responses.GET, BASE_URL, body="OK", status=200)
    responses.add(
        responses.GET, "https://www.nseindia.com/api/test", json={"ok": True}, status=200
    )

    with patch("nse.client.time.sleep"):
        session = NSESession()
        session._last_refresh = time.time() - SESSION_TTL - 10

        resp = session.get("https://www.nseindia.com/api/test", is_api=True)

    assert resp.status_code == 200
    assert len(responses.calls) == 3


@responses.activate
def test_retry_on_401():
    responses.add(responses.GET, BASE_URL, body="OK", status=200)
    responses.add(
        responses.GET, "https://www.nseindia.com/api/data", body="", status=401
    )
    responses.add(responses.GET, BASE_URL, body="OK", status=200)
    responses.add(
        responses.GET, "https://www.nseindia.com/api/data", json={"ok": True}, status=200
    )

    with patch("nse.client.time.sleep"):
        session = NSESession()
        resp = session.get("https://www.nseindia.com/api/data", is_api=True)

    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


@responses.activate
def test_no_refresh_if_session_valid():
    responses.add(responses.GET, BASE_URL, body="OK", status=200)
    responses.add(
        responses.GET, "https://www.nseindia.com/api/test", json={"ok": True}, status=200
    )

    with patch("nse.client.time.sleep"):
        session = NSESession()
        refresh_count_before = len(responses.calls)

        resp = session.get("https://www.nseindia.com/api/test", is_api=True)

    assert resp.status_code == 200
    assert len(responses.calls) == refresh_count_before + 1
