import pytest
import responses
from datetime import date
from unittest.mock import patch

from nse.bhavcopy import get_delivery_data, _parse_mto_data
from tests.conftest import SAMPLE_MTO_DATA


def test_parse_known_stocks():
    result = _parse_mto_data(SAMPLE_MTO_DATA)
    assert result["RELIANCE"] == 72.20
    assert result["TCS"] == 68.40
    assert result["INFY"] == 63.37


def test_skip_non_eq_rows():
    result = _parse_mto_data(SAMPLE_MTO_DATA)
    assert "SBIN" not in result


def test_skip_invalid_pct():
    result = _parse_mto_data(SAMPLE_MTO_DATA)
    assert "BADSTOCK" not in result


def test_hdfcbank_parsed():
    result = _parse_mto_data(SAMPLE_MTO_DATA)
    assert result["HDFCBANK"] == 68.78


@responses.activate
def test_fallback_to_previous_day(nse_session):
    # Wednesday 2024-03-20 returns 404, Tuesday 2024-03-19 has data
    wednesday_url = "https://nsearchives.nseindia.com/archives/equities/mto/MTO_20032024.DAT"
    tuesday_url = "https://nsearchives.nseindia.com/archives/equities/mto/MTO_19032024.DAT"

    responses.add(responses.GET, wednesday_url, status=404)
    responses.add(responses.GET, tuesday_url, body=SAMPLE_MTO_DATA, status=200)

    result = get_delivery_data(nse_session, for_date=date(2024, 3, 20))
    assert len(result) == 4
    assert "RELIANCE" in result


@responses.activate
def test_skip_weekends(nse_session):
    # Sunday 2024-03-24 and Saturday 2024-03-23 should be skipped
    # Friday 2024-03-22 should be tried
    friday_url = "https://nsearchives.nseindia.com/archives/equities/mto/MTO_22032024.DAT"
    responses.add(responses.GET, friday_url, body=SAMPLE_MTO_DATA, status=200)

    result = get_delivery_data(nse_session, for_date=date(2024, 3, 24))
    assert len(result) == 4
    assert "TCS" in result


@responses.activate
def test_empty_response_returns_empty_dict(nse_session):
    # Wednesday 2024-03-20, Tuesday 2024-03-19, Monday 2024-03-18 all 404
    responses.add(
        responses.GET,
        "https://nsearchives.nseindia.com/archives/equities/mto/MTO_20032024.DAT",
        status=404,
    )
    responses.add(
        responses.GET,
        "https://nsearchives.nseindia.com/archives/equities/mto/MTO_19032024.DAT",
        status=404,
    )
    responses.add(
        responses.GET,
        "https://nsearchives.nseindia.com/archives/equities/mto/MTO_18032024.DAT",
        status=404,
    )

    result = get_delivery_data(nse_session, for_date=date(2024, 3, 20), fallback_days=2)
    assert result == {}
