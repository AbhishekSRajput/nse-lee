import logging
from datetime import date, timedelta

import requests

logger = logging.getLogger(__name__)

MTO_URL_TEMPLATE = (
    "https://nsearchives.nseindia.com/archives/equities/mto/MTO_{date}.DAT"
)


def _parse_mto_data(text):
    result = {}
    for line in text.strip().splitlines():
        parts = line.split("|")
        if len(parts) < 7:
            continue
        if parts[0].strip() != "20":
            continue
        if parts[3].strip() != "EQ":
            continue

        ticker = parts[2].strip().upper()
        try:
            delivery_pct = float(parts[6].strip())
        except (ValueError, IndexError):
            continue

        if not (0 <= delivery_pct <= 100):
            logger.debug("Skipping %s: invalid delivery_pct %.2f", ticker, delivery_pct)
            continue

        result[ticker] = delivery_pct

    return result


def get_delivery_data(session, for_date=None, fallback_days=3):
    if for_date is None:
        for_date = date.today()

    for offset in range(fallback_days + 1):
        check_date = for_date - timedelta(days=offset)

        if check_date.weekday() >= 5:
            continue

        date_str = check_date.strftime("%d%m%Y")
        url = MTO_URL_TEMPLATE.format(date=date_str)

        try:
            resp = session.get(url, is_api=False)
        except requests.exceptions.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 404:
                logger.debug("MTO file not found for %s, trying previous day", check_date)
                continue
            logger.warning("HTTP error fetching MTO for %s: %s", check_date, exc)
            continue
        except Exception as exc:
            logger.warning("Error fetching MTO for %s: %s", check_date, exc)
            continue

        data = _parse_mto_data(resp.text)
        if data:
            logger.info("Delivery data: %d stocks from %s", len(data), check_date.isoformat())
            return data

    logger.warning("No delivery data found after %d fallback days", fallback_days)
    return {}
