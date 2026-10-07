"""
mock_client.py
--------------
Provides hardcoded, realistic Indian Railways data as a fallback
when the live RapidAPI endpoint is unavailable or the circuit is OPEN.

All functions in this module return data in the SAME raw structure
as the real API would, so the normalizer.py layer handles both
identically. The only difference is data_source = 'MOCK_DATA'.
"""

import logging
from datetime import datetime, timedelta

logger = logging.getLogger('tracker')

# ─────────────────────────────────────────────
# Seed data — realistic Indian trains
# ─────────────────────────────────────────────
MOCK_TRAINS = {
    "12951": {
        "train_number": "12951",
        "train_name":   "Mumbai Rajdhani Express",
        "from_station_code": "NDLS",
        "from_station_name": "New Delhi",
        "to_station_code":   "MMCT",
        "to_station_name":   "Mumbai Central",
        "departure": "16:25",
        "arrival":   "08:15",
        "duration":  "15h 50m",
        "current_station":   "RTM",
        "current_station_name": "Ratlam Junction",
        "delay_minutes": 0,
        "status":    "ON TIME",
    },
    "12301": {
        "train_number": "12301",
        "train_name":   "Howrah Rajdhani Express",
        "from_station_code": "NDLS",
        "from_station_name": "New Delhi",
        "to_station_code":   "HWH",
        "to_station_name":   "Howrah Junction",
        "departure": "16:55",
        "arrival":   "09:55",
        "duration":  "17h 00m",
        "current_station":   "ALD",
        "current_station_name": "Prayagraj Junction",
        "delay_minutes": 12,
        "status":    "DELAYED",
    },
    "12002": {
        "train_number": "12002",
        "train_name":   "New Delhi Bhopal Shatabdi Express",
        "from_station_code": "NDLS",
        "from_station_name": "New Delhi",
        "to_station_code":   "BPL",
        "to_station_name":   "Bhopal Junction",
        "departure": "06:00",
        "arrival":   "13:55",
        "duration":  "7h 55m",
        "current_station":   "AGC",
        "current_station_name": "Agra Cantt",
        "delay_minutes": 5,
        "status":    "SLIGHTLY DELAYED",
    },
    "12269": {
        "train_number": "12269",
        "train_name":   "Chennai Duronto Express",
        "from_station_code": "NDLS",
        "from_station_name": "New Delhi",
        "to_station_code":   "MAS",
        "to_station_name":   "Chennai Central",
        "departure": "07:20",
        "arrival":   "07:30",
        "duration":  "24h 10m",
        "current_station":   "BZA",
        "current_station_name": "Vijayawada Junction",
        "delay_minutes": 0,
        "status":    "ON TIME",
    },
}

MOCK_PNR = {
    "1234567890": {
        "pnr":          "1234567890",
        "train_number": "12951",
        "train_name":   "Mumbai Rajdhani Express",
        "journey_date": "2026-10-10",
        "from":         "NDLS",
        "to":           "MMCT",
        "class":        "2A",
        "passengers": [
            {"name": "Passenger 1", "coach": "A1", "berth": "32", "booking_status": "CNF"},
            {"name": "Passenger 2", "coach": "A1", "berth": "33", "booking_status": "CNF"},
        ],
    },
    "9876543210": {
        "pnr":          "9876543210",
        "train_number": "12301",
        "train_name":   "Howrah Rajdhani Express",
        "journey_date": "2026-10-12",
        "from":         "NDLS",
        "to":           "HWH",
        "class":        "3A",
        "passengers": [
            {"name": "Passenger 1", "coach": "B3", "berth": "45", "booking_status": "WL/12"},
        ],
    },
}

MOCK_SCHEDULE = {
    "12951": [
        {"station_code": "NDLS", "station_name": "New Delhi",       "arrival": "Start",  "departure": "16:25", "day": 1, "distance_km": 0},
        {"station_code": "MTJ",  "station_name": "Mathura Junction", "arrival": "17:58",  "departure": "18:00", "day": 1, "distance_km": 141},
        {"station_code": "AGC",  "station_name": "Agra Cantt",       "arrival": "18:43",  "departure": "18:45", "day": 1, "distance_km": 188},
        {"station_code": "RTM",  "station_name": "Ratlam Junction",  "arrival": "22:48",  "departure": "22:53", "day": 1, "distance_km": 543},
        {"station_code": "BRC",  "station_name": "Vadodara Junction","arrival": "01:08",  "departure": "01:13", "day": 2, "distance_km": 726},
        {"station_code": "ST",   "station_name": "Surat",            "arrival": "02:40",  "departure": "02:42", "day": 2, "distance_km": 857},
        {"station_code": "MMCT", "station_name": "Mumbai Central",   "arrival": "08:15",  "departure": "End",   "day": 2, "distance_km": 1384},
    ],
}

MOCK_BETWEEN = {
    "NDLS-MMCT": [
        {"train_number": "12951", "train_name": "Mumbai Rajdhani Express", "departure": "16:25", "arrival": "08:15", "duration": "15h 50m", "days": "Daily"},
        {"train_number": "12953", "train_name": "August Kranti Rajdhani",  "departure": "17:25", "arrival": "10:55", "duration": "17h 30m", "days": "Daily"},
        {"train_number": "12909", "train_name": "Garib Rath Express",      "departure": "15:35", "arrival": "09:30", "duration": "17h 55m", "days": "Mon,Thu,Sat"},
    ],
    "NDLS-HWH": [
        {"train_number": "12301", "train_name": "Howrah Rajdhani Express", "departure": "16:55", "arrival": "09:55", "duration": "17h 00m", "days": "Daily"},
        {"train_number": "12305", "train_name": "Poorva Express",          "departure": "22:30", "arrival": "20:10", "duration": "21h 40m", "days": "Daily"},
    ],
}


# ─────────────────────────────────────────────
# Public interface — mirrors api_client.py signatures
# ─────────────────────────────────────────────

def get_pnr_status(pnr: str) -> dict:
    logger.info(f"[MockClient] Serving mock PNR status for: {pnr}")
    data = MOCK_PNR.get(pnr.strip(), _default_pnr(pnr))
    return {"raw": data, "data_source": "MOCK_DATA"}


def get_train_status(train_number: str) -> dict:
    logger.info(f"[MockClient] Serving mock train status for: {train_number}")
    data = MOCK_TRAINS.get(train_number.strip(), _default_train(train_number))
    return {"raw": data, "data_source": "MOCK_DATA"}


def get_trains_between(from_station: str, to_station: str) -> dict:
    key = f"{from_station.upper()}-{to_station.upper()}"
    logger.info(f"[MockClient] Serving mock trains between: {key}")
    trains = MOCK_BETWEEN.get(key, _default_between(from_station, to_station))
    return {"raw": trains, "data_source": "MOCK_DATA"}


def get_train_schedule(train_number: str) -> dict:
    logger.info(f"[MockClient] Serving mock schedule for: {train_number}")
    stops = MOCK_SCHEDULE.get(train_number.strip(), _default_schedule(train_number))
    return {"raw": stops, "data_source": "MOCK_DATA"}


# ─────────────────────────────────────────────
# Default fallbacks (for unknown inputs)
# ─────────────────────────────────────────────

def _default_pnr(pnr):
    return {
        "pnr": pnr, "train_number": "N/A", "train_name": "Unknown Train",
        "journey_date": "N/A", "from": "N/A", "to": "N/A", "class": "N/A",
        "passengers": [{"name": "Unknown", "coach": "N/A", "berth": "N/A", "booking_status": "N/A"}],
    }

def _default_train(train_number):
    return {
        "train_number": train_number, "train_name": "Unknown Train",
        "from_station_code": "N/A", "from_station_name": "N/A",
        "to_station_code": "N/A", "to_station_name": "N/A",
        "departure": "N/A", "arrival": "N/A", "duration": "N/A",
        "current_station": "N/A", "current_station_name": "N/A",
        "delay_minutes": 0, "status": "UNKNOWN",
    }

def _default_between(src, dst):
    return [{"train_number": "N/A", "train_name": "No data available",
             "departure": "N/A", "arrival": "N/A", "duration": "N/A", "days": "N/A"}]

def _default_schedule(train_number):
    return [{"station_code": "N/A", "station_name": "No schedule available",
             "arrival": "N/A", "departure": "N/A", "day": 1, "distance_km": 0}]
