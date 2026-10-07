"""
normalizer.py
-------------
Transforms raw API/mock responses into a unified internal schema.

Why this exists:
  - The RapidAPI endpoint returns fields like 'trainNo', 'lateMinutes'
  - The mock client returns 'train_number', 'delay_minutes'
  - The templates should never care about the source — they always get
    the same clean keys from this layer.

Each function receives the dict returned by api_client or mock_client
and returns a clean, predictable dict safe to pass to the template.
"""

import logging
from datetime import datetime

logger = logging.getLogger('tracker')


def normalize_pnr(raw: dict, data_source: str) -> dict:
    """Map raw PNR dict → unified PNR schema."""
    try:
        # Passengers might be in "passenger" (live api) or "passengers"/"passengerList" (mock)
        passengers = raw.get("passenger", raw.get("passengers", raw.get("passengerList", [])))
        normalized_passengers = []
        for i, p in enumerate(passengers, start=1):
            normalized_passengers.append({
                "name":           p.get("passengerName", p.get("name", f"Passenger {i}")),
                "coach":          p.get("currentCoachId", p.get("coach", p.get("coachPosition", "N/A"))),
                "berth":          p.get("currentBerthNo", p.get("berth", p.get("berthNo", "N/A"))),
                "booking_status": p.get("currentStatusDisplayText", p.get("currentStatus", p.get("booking_status", "N/A"))),
            })

        # Station names might be nested dicts in live API
        boarding_station = raw.get("boarding_station", {})
        if isinstance(boarding_station, dict):
            from_station = boarding_station.get("station_name", "N/A")
        else:
            from_station = raw.get("from", raw.get("boardingPoint", "N/A"))

        reservation_upto = raw.get("reservation_upto", {})
        if isinstance(reservation_upto, dict):
            to_station = reservation_upto.get("station_name", "N/A")
        else:
            to_station = raw.get("to", raw.get("reservationUpto", "N/A"))

        result = {
            "pnr_number":   raw.get("pnr_number", raw.get("pnr", raw.get("pnrNumber", "N/A"))),
            "train_number": raw.get("train_number", raw.get("trainNumber", "N/A")),
            "train_name":   raw.get("train_name", raw.get("trainName", "N/A")),
            "journey_date": raw.get("date", raw.get("journey_date", raw.get("dateOfJourney", "N/A"))),
            "from_station": from_station,
            "to_station":   to_station,
            "travel_class": raw.get("class", raw.get("travelClass", "N/A")),
            "passengers":   normalized_passengers,
            "data_source":  data_source,
        }
        logger.debug(f"[Normalizer] PNR normalized: {result['pnr_number']}")
        return result
    except Exception as e:
        logger.error(f"[Normalizer] Error normalizing PNR: {e}")
        return _error_response(data_source, str(e))


def normalize_train_status(raw: dict, data_source: str) -> dict:
    """Map raw running status dict → unified train status schema."""
    try:
        # Check if we got the new real API format or the old mock format
        delay = raw.get("delay_in_minutes", raw.get("lateMinutes", raw.get("delay_minutes", 0)))
        if isinstance(delay, str) and delay.isdigit():
            delay = int(delay)
        elif not isinstance(delay, int):
            delay = 0

        if delay == 0:
            status_label = "ON TIME"
            status_class = "success"
        elif delay <= 10:
            status_label = f"DELAYED ({delay} min)"
            status_class = "warning"
        else:
            status_label = f"DELAYED ({delay} min)"
            status_class = "danger"

        result = {
            "train_number":        raw.get("train_number", raw.get("trainNumber", "N/A")),
            "train_name":          raw.get("train_name",   raw.get("trainName",   "N/A")),
            "source_station":      raw.get("source", raw.get("from_station_code", "N/A")),
            "source_name":         raw.get("source_stn_name", raw.get("from_station_name", "N/A")),
            "destination_station": raw.get("destination", raw.get("to_station_code", "N/A")),
            "destination_name":    raw.get("dest_stn_name", raw.get("to_station_name", "N/A")),
            "current_station":     raw.get("current_station_code", raw.get("current_station", "N/A")),
            "current_station_name":raw.get("current_station_name", "N/A"),
            "delay_minutes":       delay,
            "status_label":        status_label,
            "status_class":        status_class,
            "data_source":         data_source,
        }
        logger.debug(f"[Normalizer] Train status normalized: {result}")
        return result
    except Exception as e:
        logger.error(f"[Normalizer] Error normalizing train status: {e}")
        return _error_response(data_source, str(e))


def normalize_trains_between(raw_list: list, data_source: str) -> list:
    """Map list of raw train dicts → list of unified train dicts."""
    try:
        result = []
        for t in raw_list:
            
            # Format the run_days list into a comma-separated string if present
            run_days = t.get("run_days", t.get("runningDays", []))
            if isinstance(run_days, list):
                run_days = ", ".join(d[:3] for d in run_days)

            result.append({
                "train_number": t.get("train_number", t.get("trainNumber", "N/A")),
                "train_name":   t.get("train_name",   t.get("trainName",   "N/A")),
                "departure":    t.get("from_std",     t.get("departureTime", "N/A")),
                "arrival":      t.get("to_sta",       t.get("arrivalTime",   "N/A")),
                "duration":     t.get("duration",     t.get("travelTime",    "N/A")),
                "days":         run_days if run_days else "N/A",
                "data_source":  data_source,
            })
        logger.debug(f"[Normalizer] Between stations normalized: {len(result)} trains")
        return result
    except Exception as e:
        logger.error(f"[Normalizer] Error normalizing between stations: {e}")
        return []


def normalize_schedule(raw, data_source: str) -> list:
    """
    Map schedule response → unified stop list.
    Handles BOTH real API format (dict with 'route' list) and mock format (plain list).

    Real API fields per stop: sta, std, stationCode, stationName, distance, dayCount
    Mock fields per stop:     arrival, departure, station_code, station_name, distance_km, day
    """
    try:
        # Real API returns a dict: {"trainNumber":..., "route": [...]}
        if isinstance(raw, dict):
            stops = raw.get("route", [])
        else:
            stops = raw  # Mock returns a plain list

        result = []
        for stop in stops:
            # Convert minutes-since-midnight (sta/std) to HH:MM string
            def mins_to_time(mins):
                if mins is None or mins == -1:
                    return "N/A"
                try:
                    h, m = divmod(int(mins), 60)
                    return f"{h % 24:02d}:{m:02d}"
                except Exception:
                    return str(mins)

            result.append({
                "station_code": stop.get("stationCode",   stop.get("station_code",  "N/A")),
                "station_name": stop.get("stationName",   stop.get("station_name",  "N/A")),
                "arrival":      mins_to_time(stop.get("sta")) if "sta" in stop else stop.get("arrival", "N/A"),
                "departure":    mins_to_time(stop.get("std")) if "std" in stop else stop.get("departure", "N/A"),
                "day":          stop.get("dayCount",       stop.get("day",           1)),
                "distance_km":  stop.get("distance",       stop.get("distance_km",   0)),
                "data_source":  data_source,
            })
        logger.debug(f"[Normalizer] Schedule normalized: {len(result)} stops")
        return result
    except Exception as e:
        logger.error(f"[Normalizer] Error normalizing schedule: {e}")
        return []


def normalize_train_search(raw_list: list, data_source: str) -> list:
    """
    Normalize results from searchTrain endpoint.
    Real API fields: train_number, train_name, src_stn_code, src_stn_name,
                     dstn_stn_code, dstn_stn_name
    """
    try:
        result = []
        for t in raw_list:
            result.append({
                "train_number":        t.get("train_number",  "N/A"),
                "train_name":          t.get("train_name",    "N/A"),
                "source_station":      t.get("src_stn_code",  "N/A"),
                "source_name":         t.get("src_stn_name",  "N/A"),
                "destination_station": t.get("dstn_stn_code", "N/A"),
                "destination_name":    t.get("dstn_stn_name", "N/A"),
                "data_source":         data_source,
            })
        logger.debug(f"[Normalizer] Train search normalized: {len(result)} results")
        return result
    except Exception as e:
        logger.error(f"[Normalizer] Error normalizing train search: {e}")
        return []


def _error_response(data_source, error_msg):
    return {
        "error": True,
        "error_message": error_msg,
        "data_source": data_source,
    }
