import pytest
import responses

from nse.fo_ban import get_fo_ban_list, FO_BAN_URL
from tests.conftest import SAMPLE_FO_BAN, SAMPLE_FO_BAN_EMPTY


@responses.activate
def test_returns_ticker_list(nse_session):
    responses.add(responses.GET, FO_BAN_URL, json=SAMPLE_FO_BAN, status=200)

    result = get_fo_ban_list(nse_session)

    assert result == ["NALCO", "IBULHSGFIN", "HINDCOPPER"]


@responses.activate
def test_empty_ban_list(nse_session):
    responses.add(responses.GET, FO_BAN_URL, json=SAMPLE_FO_BAN_EMPTY, status=200)

    result = get_fo_ban_list(nse_session)
    assert result == []


@responses.activate
def test_returns_empty_on_failure(nse_session):
    responses.add(responses.GET, FO_BAN_URL, status=500)

    result = get_fo_ban_list(nse_session)
    assert result == []
