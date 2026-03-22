import pytest
import responses

from nse.option_chain import (
    get_option_summary,
    get_batch_pcr,
    _pcr_signal,
    _compute_max_pain,
    OPTION_CHAIN_URL,
)
from tests.conftest import (
    SAMPLE_OPTION_CHAIN,
    SAMPLE_OPTION_CHAIN_BULLISH,
    SAMPLE_OPTION_CHAIN_BEARISH,
)


@responses.activate
def test_pcr_calculation(nse_session):
    url = OPTION_CHAIN_URL.format(symbol="RELIANCE")
    responses.add(responses.GET, url, json=SAMPLE_OPTION_CHAIN, status=200)

    result = get_option_summary(nse_session, "RELIANCE")

    assert result is not None
    # Nearest expiry only: CE: 5000+8000+3000=16000, PE: 3000+6000+10000=19000
    assert result["total_call_oi"] == 16000
    assert result["total_put_oi"] == 19000
    assert result["pcr"] == round(19000 / 16000, 4)
    assert result["symbol"] == "RELIANCE"
    assert result["expiry"] == "28-Mar-2024"


@responses.activate
def test_max_pain_calculation(nse_session):
    url = OPTION_CHAIN_URL.format(symbol="RELIANCE")
    responses.add(responses.GET, url, json=SAMPLE_OPTION_CHAIN, status=200)

    result = get_option_summary(nse_session, "RELIANCE")

    assert result is not None
    # 3 strikes: 2800, 2850, 2900
    # At test_strike=2800:
    #   call_loss = 0 + 0 + 0 = 0 (no calls ITM)
    #   put_loss = 0 + 50*6000 + 100*10000 = 1_300_000
    #   total = 1_300_000
    # At test_strike=2850:
    #   call_loss = 50*5000 + 0 + 0 = 250_000
    #   put_loss = 0 + 0 + 50*10000 = 500_000
    #   total = 750_000
    # At test_strike=2900:
    #   call_loss = 100*5000 + 50*8000 + 0 = 900_000
    #   put_loss = 0 + 0 + 0 = 0
    #   total = 900_000
    # Min is 750_000 at strike 2850
    assert result["max_pain"] == 2850.0


def test_max_pain_standalone():
    strikes_data = {
        100.0: (1000, 500),
        110.0: (500, 2000),
        120.0: (200, 800),
    }
    # At 100: call_loss=0, put_loss=0 + 10*2000 + 20*800 = 36000 → total=36000
    # At 110: call_loss=10*1000=10000, put_loss=0 + 0 + 10*800=8000 → total=18000
    # At 120: call_loss=20*1000+10*500=25000, put_loss=0 → total=25000
    # Min is 18000 at strike 110
    assert _compute_max_pain(strikes_data) == 110.0


@responses.activate
def test_pcr_signal_bullish(nse_session):
    url = OPTION_CHAIN_URL.format(symbol="TEST")
    responses.add(responses.GET, url, json=SAMPLE_OPTION_CHAIN_BULLISH, status=200)

    result = get_option_summary(nse_session, "TEST")

    assert result is not None
    # CE: 10000+10000=20000, PE: 3000+3000=6000
    # PCR = 6000/20000 = 0.3
    assert result["pcr"] == 0.3
    assert result["pcr_signal"] == "Bullish"


@responses.activate
def test_pcr_signal_bearish(nse_session):
    url = OPTION_CHAIN_URL.format(symbol="TEST")
    responses.add(responses.GET, url, json=SAMPLE_OPTION_CHAIN_BEARISH, status=200)

    result = get_option_summary(nse_session, "TEST")

    assert result is not None
    # CE: 1000+1000=2000, PE: 5000+5000=10000
    # PCR = 10000/2000 = 5.0
    assert result["pcr"] == 5.0
    assert result["pcr_signal"] == "Bearish"


@responses.activate
def test_returns_none_on_failure(nse_session):
    url = OPTION_CHAIN_URL.format(symbol="BADSTOCK")
    responses.add(responses.GET, url, status=500)

    result = get_option_summary(nse_session, "BADSTOCK")
    assert result is None


def test_pcr_signal_thresholds():
    assert _pcr_signal(0.5) == "Bullish"
    assert _pcr_signal(0.69) == "Bullish"
    assert _pcr_signal(0.7) == "Neutral"
    assert _pcr_signal(1.0) == "Neutral"
    assert _pcr_signal(1.3) == "Neutral"
    assert _pcr_signal(1.31) == "Bearish"
    assert _pcr_signal(2.0) == "Bearish"
