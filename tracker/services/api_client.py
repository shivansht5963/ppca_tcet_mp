"""
api_client.py  (UPDATED for IRCTCAPI — irctc1.p.rapidapi.com)
--------------------------------------------------------------
Working endpoints confirmed by live testing:
  ✅ /api/v1/searchStation       — Search stations by name
  ✅ /api/v1/searchTrain         — Search trains by number/name
  ✅ /api/v1/getTrainSchedule    — Full schedule with route stops
  ❌ PNR, Running Status, Between — not available on free tier

Strategy for unavailable endpoints:
  → They throw 404, which the circuit breaker treats as a failure
  → After 3 failures the circuit OPENS
  → mock_client.py takes over for those features
  → This perfectly demonstrates the resilience pattern!
"""

import logging
import requests
import pybreaker
from django.conf import settings
from .circuit_breaker import railway_breaker

logger = logging.getLogger('tracker')

BASE_URL = f"https://{settings.RAPIDAPI_HOST}"
TIMEOUT  = 15  # seconds (increased because the free API is slow)


def _headers() -> dict:
    return {
        "X-RapidAPI-Key":  settings.RAPIDAPI_KEY,
        "X-RapidAPI-Host": settings.RAPIDAPI_HOST,
    }


# ── Working Endpoints ──────────────────────────────────

@railway_breaker
def search_station(query: str) -> dict:
    """Search for a station by name or code. Returns list of matching stations."""
    logger.info(f"[APIClient] Searching station: {query}")
    resp = requests.get(
        f"{BASE_URL}/api/v1/searchStation",
        headers=_headers(),
        params={"query": query},
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    return {"raw": data.get("data", []), "data_source": "LIVE_API"}


@railway_breaker
def search_train(query: str) -> dict:
    """Search for a train by number or name. Returns list of matching trains."""
    logger.info(f"[APIClient] Searching train: {query}")
    resp = requests.get(
        f"{BASE_URL}/api/v1/searchTrain",
        headers=_headers(),
        params={"query": query},
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    return {"raw": data.get("data", []), "data_source": "LIVE_API"}


@railway_breaker
def get_train_schedule(train_number: str) -> dict:
    """
    Fetch full schedule for a train including all route stops.
    Response includes: trainNumber, trainName, runDays, class, quota, route[]
    Each route item has: sta, std, stationCode, stationName, distance, dayCount
    """
    logger.info(f"[APIClient] Fetching schedule for train: {train_number}")
    resp = requests.get(
        f"{BASE_URL}/api/v1/getTrainSchedule",
        headers=_headers(),
        params={"trainNo": train_number},
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    return {"raw": data.get("data", {}), "data_source": "LIVE_API"}


@railway_breaker
def get_pnr_status(pnr: str) -> dict:
    """Fetch live PNR status."""
    logger.info(f"[APIClient] Fetching PNR status: {pnr}")
    resp = requests.get(
        f"{BASE_URL}/api/v2/getPNRStatus",
        headers=_headers(),
        params={"pnrNumber": pnr},
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    # PNR API often returns status: false for flushed/old PNRs
    if data.get("status") is False:
        raise ValueError(data.get("message", "Invalid PNR"))
    return {"raw": data.get("data", {}), "data_source": "LIVE_API"}


@railway_breaker
def get_train_status(train_number: str) -> dict:
    """Fetch live train running status."""
    logger.info(f"[APIClient] Fetching train running status: {train_number}")
    resp = requests.get(
        f"{BASE_URL}/api/v1/liveTrainStatus",
        headers=_headers(),
        params={"trainNo": train_number, "startDay": "1"},
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    return {"raw": data.get("data", {}), "data_source": "LIVE_API"}


@railway_breaker
def get_trains_between(from_station: str, to_station: str) -> dict:
    """Fetch live list of trains between stations."""
    logger.info(f"[APIClient] Fetching trains between: {from_station} → {to_station}")
    # Note: Requires dateOfJourney, using today's date
    from datetime import datetime
    today = datetime.today().strftime('%Y-%m-%d')
    resp = requests.get(
        f"{BASE_URL}/api/v3/trainBetweenStations",
        headers=_headers(),
        params={"fromStationCode": from_station, "toStationCode": to_station, "dateOfJourney": today},
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    return {"raw": data.get("data", []), "data_source": "LIVE_API"}
