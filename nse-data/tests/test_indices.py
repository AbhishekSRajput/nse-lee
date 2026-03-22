import pytest
import responses
from urllib.parse import quote

from nse.indices import get_sector_performance, INDEX_URL_TEMPLATE, SECTOR_INDICES
from tests.conftest import SAMPLE_INDEX, SAMPLE_VIX_INDEX


@responses.activate
def test_sector_performance(nse_session):
    # Register responses for all indices
    for idx in SECTOR_INDICES:
        url = INDEX_URL_TEMPLATE.format(index=quote(idx))
        if idx == "INDIA VIX":
            responses.add(responses.GET, url, json=SAMPLE_VIX_INDEX, status=200)
        else:
            responses.add(responses.GET, url, json=SAMPLE_INDEX, status=200)

    result = get_sector_performance(nse_session)

    assert "NIFTY BANK" in result
    assert result["NIFTY BANK"]["last"] == 48234.55
    assert result["NIFTY BANK"]["change_pct"] == 1.23
    assert result["NIFTY BANK"]["signal"] == "Strong"
    assert result["NIFTY BANK"]["advance"] == 8
    assert result["NIFTY BANK"]["decline"] == 4


@responses.activate
def test_vix_regime(nse_session):
    for idx in SECTOR_INDICES:
        url = INDEX_URL_TEMPLATE.format(index=quote(idx))
        if idx == "INDIA VIX":
            responses.add(responses.GET, url, json=SAMPLE_VIX_INDEX, status=200)
        else:
            responses.add(responses.GET, url, json=SAMPLE_INDEX, status=200)

    result = get_sector_performance(nse_session)

    assert "INDIA VIX" in result
    assert result["INDIA VIX"]["last"] == 12.5
    assert result["INDIA VIX"]["regime"] == "Risk-On"


@responses.activate
def test_individual_index_failure_does_not_fail_all(nse_session):
    for idx in SECTOR_INDICES:
        url = INDEX_URL_TEMPLATE.format(index=quote(idx))
        if idx == "NIFTY BANK":
            responses.add(responses.GET, url, status=500)
        elif idx == "INDIA VIX":
            responses.add(responses.GET, url, json=SAMPLE_VIX_INDEX, status=200)
        else:
            responses.add(responses.GET, url, json=SAMPLE_INDEX, status=200)

    result = get_sector_performance(nse_session)

    assert "NIFTY BANK" not in result
    assert "NIFTY IT" in result
    assert "INDIA VIX" in result
