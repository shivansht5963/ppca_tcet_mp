"""
api_views.py
------------
Django REST Framework API Views for the Transport Aggregator.

These sit alongside the Django template views (views.py) and expose
the same data as a proper REST API at /api/... endpoints.

Endpoints:
  GET  /api/pnr/<pnr>/                     → PNR Status
  GET  /api/train/<train_number>/status/   → Train Running Status
  GET  /api/trains/between/<from>/<to>/    → Trains Between Stations
  GET  /api/train/<train_number>/schedule/ → Train Schedule
  GET  /api/history/                       → Recent 10 Searches

All endpoints follow the circuit breaker → fallback → normalize → serialize flow.
"""

import logging
import pybreaker

from rest_framework.views    import APIView
from rest_framework.response import Response
from rest_framework          import status

from .models      import SearchHistory
from .serializers import (
    PNRSerializer,
    TrainStatusSerializer,
    TrainBetweenSerializer,
    ScheduleStopSerializer,
    SearchHistorySerializer,
)
from .services import api_client, mock_client, normalizer

logger = logging.getLogger('tracker')


# ─────────────────────────────────────────────
# Shared helper
# ─────────────────────────────────────────────

def _save_search(search_type, query, data_source):
    SearchHistory.objects.create(
        search_type=search_type,
        query=query,
        data_source=data_source,
    )


def _make_response(data, data_source, serializer_class, many=False):
    """
    Serialize normalized data and wrap in a standard response envelope.
    Returns a DRF Response with:
      {
        "success": true,
        "data_source": "LIVE_API" | "MOCK_DATA",
        "data": { ... }
      }
    """
    serializer = serializer_class(data if not many else data, many=many)
    return Response({
        "success":     True,
        "data_source": data_source,
        "data":        serializer.data if not many else serializer.data,
    }, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────
# PNR Status API
# GET /api/pnr/<pnr>/
# ─────────────────────────────────────────────

class PNRStatusAPIView(APIView):
    """
    Fetch PNR status for a given 10-digit PNR number.

    Returns passenger details, booking status (CNF/WL/RAC),
    train info and journey details.

    Falls back to mock data if the live API is unavailable.
    """

    def get(self, request, pnr):
        if not pnr.isdigit() or len(pnr) != 10:
            return Response(
                {"success": False, "error": "PNR must be a 10-digit number."},
                status=status.HTTP_400_BAD_REQUEST
            )

        data_source = 'LIVE_API'
        try:
            result      = api_client.get_pnr_status(pnr)
            raw         = result['raw']
            data_source = result['data_source']
        except (pybreaker.CircuitBreakerError, Exception) as e:
            logger.warning(f"[API:PNR] Falling back to mock. Reason: {e}")
            result      = mock_client.get_pnr_status(pnr)
            raw         = result['raw']
            data_source = result['data_source']

        normalized = normalizer.normalize_pnr(raw, data_source)
        _save_search('PNR', pnr, data_source)

        serializer = PNRSerializer(data=normalized)
        serializer.is_valid()   # Already normalized — will always be valid

        return Response({
            "success":     True,
            "data_source": data_source,
            "data":        serializer.initial_data,
        }, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────
# Train Running Status API
# GET /api/train/<train_number>/status/
# ─────────────────────────────────────────────

class TrainStatusAPIView(APIView):
    """
    Get the live running status of a train including current station,
    delay in minutes and on-time/delayed status.

    Falls back to mock data if the live API is unavailable.
    """

    def get(self, request, train_number):
        if not train_number.isdigit():
            return Response(
                {"success": False, "error": "Train number must be numeric."},
                status=status.HTTP_400_BAD_REQUEST
            )

        data_source = 'LIVE_API'
        try:
            result      = api_client.get_train_status(train_number)
            raw         = result['raw']
            data_source = result['data_source']
        except (pybreaker.CircuitBreakerError, Exception) as e:
            logger.warning(f"[API:TrainStatus] Falling back to mock. Reason: {e}")
            result      = mock_client.get_train_status(train_number)
            raw         = result['raw']
            data_source = result['data_source']

        normalized = normalizer.normalize_train_status(raw, data_source)
        _save_search('RUNNING', train_number, data_source)

        serializer = TrainStatusSerializer(data=normalized)
        serializer.is_valid()

        return Response({
            "success":     True,
            "data_source": data_source,
            "data":        serializer.initial_data,
        }, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────
# Trains Between Stations API
# GET /api/trains/between/<from_station>/<to_station>/
# ─────────────────────────────────────────────

class TrainsBetweenAPIView(APIView):
    """
    List all trains running between two station codes.

    Example: GET /api/trains/between/NDLS/MMCT/

    Falls back to mock data if the live API is unavailable.
    """

    def get(self, request, from_station, to_station):
        from_station = from_station.upper()
        to_station   = to_station.upper()
        query        = f"{from_station}-{to_station}"

        data_source = 'LIVE_API'
        try:
            result      = api_client.get_trains_between(from_station, to_station)
            raw         = result['raw']
            data_source = result['data_source']
        except (pybreaker.CircuitBreakerError, Exception) as e:
            logger.warning(f"[API:Between] Falling back to mock. Reason: {e}")
            result      = mock_client.get_trains_between(from_station, to_station)
            raw         = result['raw']
            data_source = result['data_source']

        normalized = normalizer.normalize_trains_between(raw, data_source)
        _save_search('BETWEEN', query, data_source)

        serializer = TrainBetweenSerializer(normalized, many=True)

        return Response({
            "success":     True,
            "data_source": data_source,
            "count":       len(normalized),
            "data":        serializer.data,
        }, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────
# Train Schedule API
# GET /api/train/<train_number>/schedule/
# ─────────────────────────────────────────────

class TrainScheduleAPIView(APIView):
    """
    Get the complete stop-by-stop schedule of a train.

    Returns each station with arrival/departure times, day count and
    distance from the origin.

    Falls back to mock data if the live API is unavailable.
    """

    def get(self, request, train_number):
        if not train_number.isdigit():
            return Response(
                {"success": False, "error": "Train number must be numeric."},
                status=status.HTTP_400_BAD_REQUEST
            )

        data_source = 'LIVE_API'
        try:
            result      = api_client.get_train_schedule(train_number)
            raw         = result['raw']
            data_source = result['data_source']
        except (pybreaker.CircuitBreakerError, Exception) as e:
            logger.warning(f"[API:Schedule] Falling back to mock. Reason: {e}")
            result      = mock_client.get_train_schedule(train_number)
            raw         = result['raw']
            data_source = result['data_source']

        normalized = normalizer.normalize_schedule(raw, data_source)
        _save_search('SCHEDULE', train_number, data_source)

        serializer = ScheduleStopSerializer(normalized, many=True)

        return Response({
            "success":     True,
            "data_source": data_source,
            "total_stops": len(normalized),
            "data":        serializer.data,
        }, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────
# Search History API
# GET /api/history/
# ─────────────────────────────────────────────

class SearchHistoryAPIView(APIView):
    """
    Returns the last 10 searches made by any user.

    Useful for the dashboard's recent searches feature
    and for debugging which data sources were served.
    """

    def get(self, request):
        recent     = SearchHistory.objects.all()[:10]
        serializer = SearchHistorySerializer(recent, many=True)

        return Response({
            "success": True,
            "count":   len(serializer.data),
            "data":    serializer.data,
        }, status=status.HTTP_200_OK)
