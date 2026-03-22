import pytest

from nse.client import NSESession
from nse.bhavcopy import get_delivery_data
from nse.fii_dii import get_fii_dii
from nse.fo_ban import get_fo_ban_list


@pytest.mark.integration
def test_real_delivery_fetch():
    session = NSESession()
    data = get_delivery_data(session)
    assert isinstance(data, dict)
    assert len(data) > 1000, f"Expected > 1000 stocks, got {len(data)}"
    # Spot-check a blue chip
    assert any(
        ticker in data for ticker in ("RELIANCE", "TCS", "HDFCBANK", "INFY")
    ), "No blue-chip tickers found in delivery data"


@pytest.mark.integration
def test_real_fii_dii():
    session = NSESession()
    result = get_fii_dii(session)
    if result is not None:
        for key in ("fii_buy_cr", "fii_sell_cr", "fii_net_cr", "dii_buy_cr", "dii_sell_cr", "dii_net_cr"):
            assert key in result, f"Missing key: {key}"
        assert result["fii_signal"] in ("Buying", "Selling", "Neutral")
        assert result["dii_signal"] in ("Buying", "Selling", "Neutral")


@pytest.mark.integration
def test_real_fo_ban():
    session = NSESession()
    result = get_fo_ban_list(session)
    assert isinstance(result, list)
    for ticker in result:
        assert ticker == ticker.upper()
