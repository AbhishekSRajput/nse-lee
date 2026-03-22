import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote

logger = logging.getLogger(__name__)

INDEX_URL_TEMPLATE = "https://www.nseindia.com/api/equity-stockIndices?index={index}"

SECTOR_INDICES = [
    "NIFTY BANK",
    "NIFTY IT",
    "NIFTY PHARMA",
    "NIFTY AUTO",
    "NIFTY FMCG",
    "NIFTY METAL",
    "NIFTY REALTY",
    "NIFTY INFRA",
    "NIFTY PSU BANK",
    "NIFTY MEDIA",
    "NIFTY ENERGY",
    "INDIA VIX",
]


def _sector_signal(change_pct):
    if change_pct > 1:
        return "Strong"
    elif change_pct < -1:
        return "Weak"
    return "Neutral"


def _vix_regime(vix_value):
    if vix_value > 22:
        return "Risk-Off"
    elif vix_value > 18:
        return "Elevated"
    elif vix_value < 14:
        return "Risk-On"
    return "Neutral"


def _fetch_single_index(session, index_name):
    url = INDEX_URL_TEMPLATE.format(index=quote(index_name))
    try:
        resp = session.get(url, is_api=True)
        data = resp.json()
    except Exception as exc:
        logger.warning("Failed to fetch index %s: %s", index_name, exc)
        return index_name, None

    try:
        items = data.get("data", [])
        if not items:
            return index_name, None

        first = items[0]
        last = float(first.get("last", first.get("lastPrice", 0)))
        change_pct = float(first.get("pChange", first.get("percentChange", 0)))

        if index_name == "INDIA VIX":
            return index_name, {
                "last": last,
                "change_pct": round(change_pct, 2),
                "regime": _vix_regime(last),
            }

        advance = int(first.get("advances", 0))
        decline = int(first.get("declines", 0))

        return index_name, {
            "last": last,
            "change_pct": round(change_pct, 2),
            "advance": advance,
            "decline": decline,
            "signal": _sector_signal(change_pct),
        }

    except Exception as exc:
        logger.warning("Failed to parse index %s: %s", index_name, exc)
        return index_name, None


def get_sector_performance(session):
    result = {}

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(_fetch_single_index, session, idx): idx
            for idx in SECTOR_INDICES
        }

        for future in as_completed(futures, timeout=10):
            try:
                index_name, data = future.result()
                if data is not None:
                    result[index_name] = data
            except Exception as exc:
                idx = futures[future]
                logger.warning("Index fetch failed for %s: %s", idx, exc)

    return result
