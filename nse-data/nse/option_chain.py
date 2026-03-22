import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote

logger = logging.getLogger(__name__)

OPTION_CHAIN_URL = "https://www.nseindia.com/api/option-chain-equities?symbol={symbol}"


def _pcr_signal(pcr):
    if pcr < 0.7:
        return "Bullish"
    elif pcr > 1.3:
        return "Bearish"
    return "Neutral"


def _compute_max_pain(strikes_data):
    if not strikes_data:
        return 0.0

    strike_prices = sorted(strikes_data.keys())
    min_pain = float("inf")
    max_pain_strike = strike_prices[0]

    for test_strike in strike_prices:
        total_pain = 0.0
        for strike, (call_oi, put_oi) in strikes_data.items():
            call_loss = max(0, test_strike - strike) * call_oi
            put_loss = max(0, strike - test_strike) * put_oi
            total_pain += call_loss + put_loss

        if total_pain < min_pain:
            min_pain = total_pain
            max_pain_strike = test_strike

    return float(max_pain_strike)


def get_option_summary(session, symbol):
    url = OPTION_CHAIN_URL.format(symbol=quote(symbol.upper()))

    try:
        resp = session.get(url, is_api=True)
        data = resp.json()
    except Exception as exc:
        logger.debug("Failed to fetch option chain for %s: %s", symbol, exc)
        return None

    try:
        records = data.get("records", {})
        expiry_dates = records.get("expiryDates", [])
        if not expiry_dates:
            return None

        nearest_expiry = expiry_dates[0]
        all_data = records.get("data", [])

        total_call_oi = 0
        total_put_oi = 0
        strikes_data = {}

        for item in all_data:
            if item.get("expiryDate") != nearest_expiry:
                continue

            strike = float(item.get("strikePrice", 0))
            call_oi = int(item.get("CE", {}).get("openInterest", 0))
            put_oi = int(item.get("PE", {}).get("openInterest", 0))

            total_call_oi += call_oi
            total_put_oi += put_oi
            strikes_data[strike] = (call_oi, put_oi)

        if total_call_oi == 0:
            return None

        pcr = round(total_put_oi / total_call_oi, 4)
        max_pain = _compute_max_pain(strikes_data)

        return {
            "symbol": symbol.upper(),
            "expiry": nearest_expiry,
            "pcr": pcr,
            "max_pain": max_pain,
            "total_call_oi": total_call_oi,
            "total_put_oi": total_put_oi,
            "pcr_signal": _pcr_signal(pcr),
        }

    except Exception as exc:
        logger.warning("Failed to parse option chain for %s: %s", symbol, exc)
        return None


def get_batch_pcr(session, symbols):
    result = {}

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(get_option_summary, session, sym): sym
            for sym in symbols
        }

        for future in as_completed(futures, timeout=30):
            sym = futures[future]
            try:
                summary = future.result()
                if summary is not None:
                    result[sym.upper()] = summary
            except Exception as exc:
                logger.debug("Option chain fetch failed for %s: %s", sym, exc)

    return result
