import pytest
import responses
from datetime import date, timedelta
from unittest.mock import patch

from nse.corporate_actions import (
    get_corporate_actions,
    get_earnings_tickers,
    _classify_action,
    _parse_date,
    CORPORATE_ACTIONS_URL,
)
from tests.conftest import SAMPLE_CORPORATE_ACTIONS


def test_earnings_detection():
    assert _classify_action("Quarterly Results/Financial Results") == "EARNINGS"
    assert _classify_action("Board Meeting - Annual Result") == "EARNINGS"
    assert _classify_action("Financial Result for Q3") == "EARNINGS"


def test_dividend_detection():
    assert _classify_action("Interim Dividend - Rs 5 Per Share") == "DIVIDEND"
    assert _classify_action("Final Dividend Rs 10") == "DIVIDEND"


def test_bonus_detection():
    assert _classify_action("Bonus Issue 1:1") == "BONUS"


def test_split_detection():
    assert _classify_action("Stock Split from Rs 10 to Rs 2") == "SPLIT"


def test_buyback_detection():
    assert _classify_action("Buy Back of Shares") == "BUYBACK"


def test_other_detection():
    assert _classify_action("Some random corporate event") == "OTHER"


def test_date_parsing_both_formats():
    d1 = _parse_date("22-Mar-2024")
    assert d1 == date(2024, 3, 22)

    d2 = _parse_date("22-03-2024")
    assert d2 == date(2024, 3, 22)


def test_date_parsing_invalid():
    assert _parse_date("invalid-date") is None


@responses.activate
def test_get_corporate_actions(nse_session):
    responses.add(
        responses.GET,
        CORPORATE_ACTIONS_URL,
        json=SAMPLE_CORPORATE_ACTIONS,
        status=200,
    )

    result = get_corporate_actions(nse_session)

    assert len(result) == 6
    assert result[0]["ticker"] == "TCS"
    assert result[0]["action_type"] == "EARNINGS"
    assert result[0]["ex_date"] == "2024-03-25"


def test_get_earnings_tickers_within_3_days():
    today = date.today()
    actions = [
        {
            "ticker": "TCS",
            "action_type": "EARNINGS",
            "ex_date": (today + timedelta(days=1)).isoformat(),
            "details": "Quarterly Results",
        },
        {
            "ticker": "INFY",
            "action_type": "EARNINGS",
            "ex_date": (today + timedelta(days=2)).isoformat(),
            "details": "Annual Results",
        },
        {
            "ticker": "RELIANCE",
            "action_type": "DIVIDEND",
            "ex_date": (today + timedelta(days=1)).isoformat(),
            "details": "Interim Dividend",
        },
    ]

    result = get_earnings_tickers(actions, within_days=3)
    assert result == {"TCS", "INFY"}


def test_get_earnings_tickers_excludes_far_dates():
    today = date.today()
    actions = [
        {
            "ticker": "TCS",
            "action_type": "EARNINGS",
            "ex_date": (today + timedelta(days=10)).isoformat(),
            "details": "Quarterly Results",
        },
        {
            "ticker": "INFY",
            "action_type": "EARNINGS",
            "ex_date": (today + timedelta(days=1)).isoformat(),
            "details": "Annual Results",
        },
    ]

    result = get_earnings_tickers(actions, within_days=3)
    assert result == {"INFY"}
    assert "TCS" not in result
