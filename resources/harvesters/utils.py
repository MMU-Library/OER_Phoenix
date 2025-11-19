import time
import logging
import requests

logger = logging.getLogger(__name__)


def request_with_retry(method, url, headers=None, params=None, timeout=15, max_attempts=3, backoff_factor=2):
    """Perform an HTTP request with simple retry/backoff for transient errors.

    Returns the requests.Response on success or raises the last exception on failure.
    """
    attempts = 0
    last_exc = None
    while attempts < max_attempts:
        attempts += 1
        try:
            if method.lower() == 'get':
                resp = requests.get(url, headers=headers or {}, params=params or {}, timeout=timeout)
            elif method.lower() == 'head':
                resp = requests.head(url, headers=headers or {}, params=params or {}, timeout=timeout)
            else:
                resp = requests.request(method, url, headers=headers or {}, params=params or {}, timeout=timeout)

            # Retry on 5xx or 429
            if resp.status_code == 429 or 500 <= resp.status_code < 600:
                logger.warning("Request %s %s attempt %d returned %d, retrying...", method, url, attempts, resp.status_code)
                time.sleep(backoff_factor ** attempts)
                last_exc = requests.HTTPError(f"status {resp.status_code}")
                continue

            return resp

        except requests.RequestException as e:
            last_exc = e
            logger.warning("Request %s %s attempt %d failed: %s", method, url, attempts, e)
            time.sleep(backoff_factor ** attempts)
            continue

    # If we get here, all attempts failed
    if last_exc:
        raise last_exc
    raise requests.RequestException("Unknown request failure")
