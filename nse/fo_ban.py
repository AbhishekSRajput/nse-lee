import logging

import requests

logger = logging.getLogger(__name__)

FO_BAN_URL = "https://www.nseindia.com/api/fo-banlist"


def get_fo_ban_list(session):
    try:
        resp = session.get(FO_BAN_URL, is_api=True)
        data = resp.json()
    except requests.exceptions.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            logger.debug("F&O ban list returned 404 — no stocks in ban period")
            return []
        logger.warning("Failed to fetch F&O ban list: %s", exc)
        return []
    except Exception as exc:
        logger.warning("Failed to fetch F&O ban list: %s", exc)
        return []

    try:
        items = data.get("data", [])
        return [item["tradingSymbol"].upper() for item in items if "tradingSymbol" in item]
    except Exception as exc:
        logger.warning("Failed to parse F&O ban list: %s", exc)
        return []
