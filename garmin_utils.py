import time

from garminconnect import Garmin, GarminConnectTooManyRequestsError

_GARTH_DIR = "/tmp/garth_tokens"
_RETRY_DELAYS = [60, 120, 240]


def login_garmin(email: str, password: str) -> Garmin:
    """Login to Garmin Connect, reusing cached tokens when available.

    Falls back to username/password login and retries with exponential backoff
    on rate limit errors.
    """
    client = Garmin(email, password, garth_dir=_GARTH_DIR)
    last_exc: GarminConnectTooManyRequestsError | None = None
    for delay in [0] + _RETRY_DELAYS:
        if delay:
            print(f"Rate limited by Garmin. Waiting {delay}s before retry...")
            time.sleep(delay)
        try:
            client.login()
            return client
        except GarminConnectTooManyRequestsError as exc:
            last_exc = exc
    raise last_exc or RuntimeError("Failed to login to Garmin Connect")
