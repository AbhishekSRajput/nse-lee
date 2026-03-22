import time
import logging
import threading

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://www.nseindia.com"
SESSION_TTL = 13 * 60  # 13 minutes in seconds

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "sec-ch-ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
}

API_HEADERS = {
    "X-Requested-With": "XMLHttpRequest",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}


class NSESession:
    def __init__(self):
        self._session = requests.Session()
        self._session.headers.update(BROWSER_HEADERS)
        self._last_refresh = 0.0
        self._lock = threading.Lock()
        self.refresh()

    def refresh(self):
        with self._lock:
            resp = self._session.get(BASE_URL, timeout=10)
            resp.raise_for_status()
            time.sleep(0.6)
            self._last_refresh = time.time()
            cookie_names = [c.name for c in self._session.cookies]
            logger.debug("Session refreshed. Cookies: %s", cookie_names)

    def _is_session_valid(self):
        if self._last_refresh == 0.0:
            return False
        return (time.time() - self._last_refresh) < SESSION_TTL

    def _ensure_session(self):
        if not self._is_session_valid():
            logger.info("Session expired, refreshing...")
            self.refresh()

    def get(self, url, is_api=False, max_retries=2, **kwargs):
        self._ensure_session()

        headers = {"Referer": BASE_URL}
        if is_api:
            headers.update(API_HEADERS)

        kwargs.setdefault("timeout", 10)
        kwargs.setdefault("headers", {})
        kwargs["headers"].update(headers)

        last_exc = None
        for attempt in range(max_retries):
            try:
                resp = self._session.get(url, **kwargs)

                if resp.status_code in (401, 403):
                    logger.warning(
                        "Got %d on attempt %d, refreshing session...",
                        resp.status_code,
                        attempt + 1,
                    )
                    self.refresh()
                    continue

                resp.raise_for_status()
                return resp

            except requests.exceptions.Timeout as exc:
                last_exc = exc
                logger.warning(
                    "Timeout on attempt %d for %s", attempt + 1, url
                )
                if attempt < max_retries - 1:
                    time.sleep(1)
                continue

            except requests.exceptions.HTTPError as exc:
                if exc.response is not None and exc.response.status_code == 404:
                    raise
                last_exc = exc
                if attempt < max_retries - 1:
                    time.sleep(1)
                continue

        if last_exc:
            raise last_exc
        raise requests.exceptions.RequestException(
            f"Failed after {max_retries} retries for {url}"
        )
