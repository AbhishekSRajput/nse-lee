import pytest
import responses
from unittest.mock import patch

from nse.fii_dii import get_fii_dii, FII_DII_URL, _parse_value
from tests.conftest import SAMPLE_FII_DII, SAMPLE_FII_DII_SELLING


@responses.activate
def test_parse_fii_buying(nse_session):
    responses.add(responses.GET, FII_DII_URL, json=SAMPLE_FII_DII, status=200)

    result = get_fii_dii(nse_session)

    assert result is not None
    assert result["fii_net_cr"] == 2111.11
    assert result["fii_signal"] == "Buying"


@responses.activate
def test_parse_fii_selling(nse_session):
    responses.add(responses.GET, FII_DII_URL, json=SAMPLE_FII_DII_SELLING, status=200)

    result = get_fii_dii(nse_session)

    assert result is not None
    assert result["fii_net_cr"] == -3500.0
    assert result["fii_signal"] == "Selling"
    assert result["dii_net_cr"] == 1500.0
    assert result["dii_signal"] == "Buying"


def test_handles_comma_formatted_numbers():
    assert _parse_value("12,345.67") == 12345.67
    assert _parse_value("1,23,456.78") == 123456.78
    assert _parse_value("100.50") == 100.50


@responses.activate
def test_returns_none_on_http_error(nse_session):
    responses.add(responses.GET, FII_DII_URL, status=500)

    result = get_fii_dii(nse_session)
    assert result is None
