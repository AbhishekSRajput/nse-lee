import logging
from datetime import date, datetime, timedelta

logger = logging.getLogger(__name__)

CORPORATE_ACTIONS_URL = "https://www.nseindia.com/api/corporates-corporateActions"


def _classify_action(purpose):
    purpose_lower = purpose.lower()
    for keyword in ("quarterly result", "annual result", "financial result", "board meeting"):
        if keyword in purpose_lower:
            return "EARNINGS"
    if "dividend" in purpose_lower:
        return "DIVIDEND"
    if "bonus" in purpose_lower:
        return "BONUS"
    if "stock split" in purpose_lower or "split" in purpose_lower:
        return "SPLIT"
    if "buy back" in purpose_lower or "buyback" in purpose_lower:
        return "BUYBACK"
    return "OTHER"


def _parse_date(date_str):
    for fmt in ("%d-%b-%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None


def get_corporate_actions(session, days_ahead=15):
    today = date.today()
    end_date = today + timedelta(days=days_ahead)

    from_str = today.strftime("%d-%m-%Y")
    to_str = end_date.strftime("%d-%m-%Y")

    url = (
        f"{CORPORATE_ACTIONS_URL}"
        f"?index=equities&from_date={from_str}&to_date={to_str}"
    )

    try:
        resp = session.get(url, is_api=True)
        data = resp.json()
    except Exception as exc:
        logger.warning("Failed to fetch corporate actions: %s", exc)
        return []

    actions = []
    try:
        for item in data:
            ticker = item.get("symbol", "").upper()
            purpose = item.get("purpose", "")
            ex_date_str = item.get("exDate", "")

            parsed_date = _parse_date(ex_date_str)
            if parsed_date is None:
                logger.debug("Skipping action for %s: unparseable date %s", ticker, ex_date_str)
                continue

            actions.append({
                "ticker": ticker,
                "action_type": _classify_action(purpose),
                "ex_date": parsed_date.isoformat(),
                "details": purpose,
            })
    except Exception as exc:
        logger.warning("Failed to parse corporate actions: %s", exc)
        return []

    return actions


def get_earnings_tickers(actions, within_days=3):
    today = date.today()
    cutoff = today + timedelta(days=within_days)
    result = set()

    for action in actions:
        if action["action_type"] != "EARNINGS":
            continue
        try:
            ex_date = date.fromisoformat(action["ex_date"])
        except (ValueError, KeyError):
            continue
        if today <= ex_date <= cutoff:
            result.add(action["ticker"])

    return result
