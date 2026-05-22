import os
import time
from pathlib import Path

from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)

_cached_client = None

# Garmin's Cloudflare blocks garth's default mobile User-Agent (GCM-iOS-5.7.2.1).
# Override with a browser User-Agent to bypass this.
# See: https://github.com/matin/garth/discussions/222
_BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)


def _set_browser_user_agent(garmin: Garmin) -> None:
    garmin.garth.sess.headers["User-Agent"] = _BROWSER_USER_AGENT


def get_garmin_client() -> Garmin:
    """Return a logged-in Garmin client, reusing saved tokens when available.

    Caches the client in memory so subsequent calls within the same process
    return the same instance without re-authenticating. For standalone use,
    also persists tokens to disk via the GARMINTOKENS env var (default
    ~/.garminconnect).
    """
    global _cached_client
    if _cached_client is not None:
        return _cached_client

    tokenstore = os.getenv("GARMINTOKENS", "~/.garminconnect")
    tokenstore_path = str(Path(tokenstore).expanduser())

    # Try loading saved tokens first (no re-authentication needed)
    try:
        garmin = Garmin()
        _set_browser_user_agent(garmin)
        garmin.login(tokenstore_path)
        _cached_client = garmin
        return garmin
    except (
        FileNotFoundError,
        GarminConnectAuthenticationError,
        GarminConnectConnectionError,
    ):
        pass

    # Fall back to credential login with retry on 429 errors
    email = os.getenv("GARMIN_EMAIL")
    password = os.getenv("GARMIN_PASSWORD")

    max_retries = 3
    delays = [10, 30, 90]

    for attempt in range(max_retries):
        try:
            garmin = Garmin(email=email, password=password)
            _set_browser_user_agent(garmin)
            garmin.login(tokenstore_path)
            _cached_client = garmin
            return garmin
        except GarminConnectTooManyRequestsError as e:
            if attempt < max_retries - 1:
                delay = delays[attempt]
                print(f"Rate limited (429), retrying in {delay}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(delay)
            else:
                raise
        except (GarminConnectConnectionError, GarminConnectAuthenticationError) as e:
            if "429" in str(e) and attempt < max_retries - 1:
                delay = delays[attempt]
                print(f"Rate limited (429), retrying in {delay}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(delay)
            else:
                raise
