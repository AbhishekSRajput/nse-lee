import logging
from datetime import date

logger = logging.getLogger(__name__)

FII_DII_URL = "https://www.nseindia.com/api/fiidiiTradeReact"


def _parse_value(s):
    return float(s.replace(",", ""))


def _compute_signal(net_cr):
    if net_cr > 500:
        return "Buying"
    elif net_cr < -500:
        return "Selling"
    return "Neutral"


def get_fii_dii(session):
    try:
        resp = session.get(FII_DII_URL, is_api=True)
        data = resp.json()
    except Exception as exc:
        logger.warning("Failed to fetch FII/DII data: %s", exc)
        return None

    try:
        fii_buy = 0.0
        fii_sell = 0.0
        dii_buy = 0.0
        dii_sell = 0.0

        for row in data:
            category = row.get("category", "").upper()
            buy_val = _parse_value(row.get("buyValue", "0"))
            sell_val = _parse_value(row.get("sellValue", "0"))

            if "FII" in category or "FPI" in category:
                fii_buy += buy_val
                fii_sell += sell_val
            elif "DII" in category:
                dii_buy += buy_val
                dii_sell += sell_val

        fii_net = round(fii_buy - fii_sell, 2)
        dii_net = round(dii_buy - dii_sell, 2)

        return {
            "date": date.today().isoformat(),
            "fii_buy_cr": round(fii_buy, 2),
            "fii_sell_cr": round(fii_sell, 2),
            "fii_net_cr": fii_net,
            "dii_buy_cr": round(dii_buy, 2),
            "dii_sell_cr": round(dii_sell, 2),
            "dii_net_cr": dii_net,
            "fii_signal": _compute_signal(fii_net),
            "dii_signal": _compute_signal(dii_net),
        }

    except Exception as exc:
        logger.warning("Failed to parse FII/DII data: %s", exc)
        return None
