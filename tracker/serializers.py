"""
serializers.py
--------------
DRF Serializers for the Resilient Public Transport Aggregator.

These serializers define the shape of data returned by the DRF API endpoints.
They work with the normalized data (already processed by normalizer.py) and
ensure type-safe, well-documented API responses for each transport feature.

Serializer hierarchy:
  PassengerSerializer       → nested inside PNRSerializer
  PNRSerializer             → /api/pnr/<pnr>/
  TrainStatusSerializer     → /api/train/<number>/status/
  TrainBetweenSerializer    → /api/trains/between/<from>/<to>/
  ScheduleStopSerializer    → /api/train/<number>/schedule/
  SearchHistorySerializer   → /api/history/
"""

from rest_framework import serializers
from .models import SearchHistory


# ─────────────────────────────────────────────
# PNR Serializers
# ─────────────────────────────────────────────

class PassengerSerializer(serializers.Serializer):
    """Represents a single passenger in a PNR."""
    name           = serializers.CharField()
    coach          = serializers.CharField()
    berth          = serializers.CharField()
    booking_status = serializers.CharField()


class PNRSerializer(serializers.Serializer):
    """Full PNR status response — normalized from any API source."""
    pnr_number   = serializers.CharField()
    train_number = serializers.CharField()
    train_name   = serializers.CharField()
    journey_date = serializers.CharField()
    from_station = serializers.CharField()
    to_station   = serializers.CharField()
    travel_class = serializers.CharField()
    passengers   = PassengerSerializer(many=True)
    data_source  = serializers.ChoiceField(choices=['LIVE_API', 'MOCK_DATA'])


# ─────────────────────────────────────────────
# Train Running Status Serializer
# ─────────────────────────────────────────────

class TrainStatusSerializer(serializers.Serializer):
    """Live running status of a train."""
    train_number         = serializers.CharField()
    train_name           = serializers.CharField()
    source_station       = serializers.CharField()
    source_name          = serializers.CharField()
    destination_station  = serializers.CharField()
    destination_name     = serializers.CharField()
    current_station      = serializers.CharField()
    current_station_name = serializers.CharField()
    delay_minutes        = serializers.IntegerField()
    status_label         = serializers.CharField()
    status_class         = serializers.ChoiceField(choices=['success', 'warning', 'danger'])
    data_source          = serializers.ChoiceField(choices=['LIVE_API', 'MOCK_DATA'])


# ─────────────────────────────────────────────
# Trains Between Stations Serializer
# ─────────────────────────────────────────────

class TrainBetweenSerializer(serializers.Serializer):
    """A single train entry in a between-stations search result."""
    train_number = serializers.CharField()
    train_name   = serializers.CharField()
    departure    = serializers.CharField()
    arrival      = serializers.CharField()
    duration     = serializers.CharField()
    days         = serializers.CharField()
    data_source  = serializers.ChoiceField(choices=['LIVE_API', 'MOCK_DATA'])


# ─────────────────────────────────────────────
# Train Schedule Serializer
# ─────────────────────────────────────────────

class ScheduleStopSerializer(serializers.Serializer):
    """A single stop (station) in a train's schedule."""
    station_code = serializers.CharField()
    station_name = serializers.CharField()
    arrival      = serializers.CharField()
    departure    = serializers.CharField()
    day          = serializers.IntegerField()
    distance_km  = serializers.IntegerField()
    data_source  = serializers.ChoiceField(choices=['LIVE_API', 'MOCK_DATA'])


# ─────────────────────────────────────────────
# Search History Serializer (from Django Model)
# ─────────────────────────────────────────────

class SearchHistorySerializer(serializers.ModelSerializer):
    """Serializes SearchHistory model for /api/history/ endpoint."""
    search_type_display = serializers.CharField(
        source='get_search_type_display',
        read_only=True
    )

    class Meta:
        model  = SearchHistory
        fields = [
            'id',
            'search_type',
            'search_type_display',
            'query',
            'data_source',
            'timestamp',
        ]
        read_only_fields = ['id', 'timestamp', 'search_type_display']


# ─────────────────────────────────────────────
# API Response Envelope Serializers
# (wraps data + metadata in a consistent response structure)
# ─────────────────────────────────────────────

class APIResponseSerializer(serializers.Serializer):
    """
    Standard envelope for every API response.
    Ensures consistent JSON structure for all endpoints:
    {
        "success": true,
        "data_source": "LIVE_API" | "MOCK_DATA",
        "data": { ... }
    }
    """
    success     = serializers.BooleanField(default=True)
    data_source = serializers.ChoiceField(choices=['LIVE_API', 'MOCK_DATA'])
    message     = serializers.CharField(required=False, allow_blank=True)
