"""
views.py
--------
Django views for the Resilient Public Transport Information Aggregator.

Flow for every search:
  1. Validate form input
  2. Try live API (api_client.py) — wrapped in circuit breaker
  3. On failure (requests error, timeout, CircuitBreakerError) → fallback to mock_client.py
  4. Pass raw result through normalizer.py
  5. Save search to SearchHistory
  6. Render result template with normalized data + data_source flag
"""

import logging
import pybreaker
from django.shortcuts import render, redirect
from django.utils import timezone

from .models import SearchHistory
from .services import api_client, mock_client, normalizer

logger = logging.getLogger('tracker')


# ─────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────

def _get_recent_searches():
    qs = SearchHistory.objects.all()[:50]
    seen = set()
    unique = []
    for s in qs:
        key = (s.search_type, s.query)
        if key not in seen:
            seen.add(key)
            unique.append(s)
            if len(unique) == 10:
                break
    return unique


def _save_search(search_type: str, query: str, data_source: str):
    SearchHistory.objects.create(
        search_type=search_type,
        query=query,
        data_source=data_source,
    )


# ─────────────────────────────────────────────
# Dashboard — Home Page
# ─────────────────────────────────────────────

def dashboard(request):
    recent = _get_recent_searches()
    return render(request, 'tracker/dashboard.html', {
        'recent_searches': recent,
        'page_title': 'RailTrack India — Transport Aggregator',
    })


# ─────────────────────────────────────────────
# PNR Status
# ─────────────────────────────────────────────

def pnr_status(request):
    if request.method != 'POST':
        return redirect('dashboard')

    pnr = request.POST.get('pnr', '').strip()
    if not pnr or len(pnr) != 10 or not pnr.isdigit():
        return render(request, 'tracker/dashboard.html', {
            'error': 'Please enter a valid 10-digit PNR number.',
            'recent_searches': _get_recent_searches(),
        })

    data_source = 'LIVE_API'
    try:
        result = api_client.get_pnr_status(pnr)
        raw         = result['raw']
        data_source = result['data_source']
    except (pybreaker.CircuitBreakerError, Exception) as e:
        logger.warning(f"[View:PNR] Falling back to mock. Reason: {e}")
        result      = mock_client.get_pnr_status(pnr)
        raw         = result['raw']
        data_source = result['data_source']

    normalized = normalizer.normalize_pnr(raw, data_source)
    _save_search('PNR', pnr, data_source)

    return render(request, 'tracker/pnr_result.html', {
        'result':      normalized,
        'data_source': data_source,
        'page_title':  f'PNR {pnr} Status — RailTrack India',
    })


# ─────────────────────────────────────────────
# Train Running Status
# ─────────────────────────────────────────────

def train_status(request):
    if request.method != 'POST':
        return redirect('dashboard')

    train_number = request.POST.get('train_number', '').strip()
    if not train_number or not train_number.isdigit():
        return render(request, 'tracker/dashboard.html', {
            'error': 'Please enter a valid numeric train number.',
            'recent_searches': _get_recent_searches(),
        })

    data_source = 'LIVE_API'
    try:
        result      = api_client.get_train_status(train_number)
        raw         = result['raw']
        data_source = result['data_source']
    except (pybreaker.CircuitBreakerError, Exception) as e:
        logger.warning(f"[View:TrainStatus] Falling back to mock. Reason: {e}")
        result      = mock_client.get_train_status(train_number)
        raw         = result['raw']
        data_source = result['data_source']

    normalized = normalizer.normalize_train_status(raw, data_source)
    _save_search('RUNNING', train_number, data_source)

    return render(request, 'tracker/train_status.html', {
        'result':      normalized,
        'data_source': data_source,
        'page_title':  f'Train {train_number} Status — RailTrack India',
    })


# ─────────────────────────────────────────────
# Trains Between Stations
# ─────────────────────────────────────────────

def trains_between(request):
    if request.method != 'POST':
        return redirect('dashboard')

    from_station = request.POST.get('from_station', '').strip().upper()
    to_station   = request.POST.get('to_station',   '').strip().upper()

    if not from_station or not to_station:
        return render(request, 'tracker/dashboard.html', {
            'error': 'Please enter both source and destination station codes.',
            'recent_searches': _get_recent_searches(),
        })

    query       = f"{from_station}-{to_station}"
    data_source = 'LIVE_API'
    try:
        result      = api_client.get_trains_between(from_station, to_station)
        raw         = result['raw']
        data_source = result['data_source']
    except (pybreaker.CircuitBreakerError, Exception) as e:
        logger.warning(f"[View:TrainsBetween] Falling back to mock. Reason: {e}")
        result      = mock_client.get_trains_between(from_station, to_station)
        raw         = result['raw']
        data_source = result['data_source']

    normalized = normalizer.normalize_trains_between(raw, data_source)
    _save_search('BETWEEN', query, data_source)

    return render(request, 'tracker/trains_between.html', {
        'trains':        normalized,
        'from_station':  from_station,
        'to_station':    to_station,
        'data_source':   data_source,
        'page_title':    f'Trains {from_station}→{to_station} — RailTrack India',
    })


# ─────────────────────────────────────────────
# Train Schedule
# ─────────────────────────────────────────────

def train_schedule(request):
    if request.method != 'POST':
        return redirect('dashboard')

    train_number = request.POST.get('train_number', '').strip()
    if not train_number or not train_number.isdigit():
        return render(request, 'tracker/dashboard.html', {
            'error': 'Please enter a valid numeric train number.',
            'recent_searches': _get_recent_searches(),
        })

    data_source = 'LIVE_API'
    try:
        result      = api_client.get_train_schedule(train_number)
        raw         = result['raw']
        data_source = result['data_source']
    except (pybreaker.CircuitBreakerError, Exception) as e:
        logger.warning(f"[View:Schedule] Falling back to mock. Reason: {e}")
        result      = mock_client.get_train_schedule(train_number)
        raw         = result['raw']
        data_source = result['data_source']

    normalized = normalizer.normalize_schedule(raw, data_source)
    _save_search('SCHEDULE', train_number, data_source)

    return render(request, 'tracker/train_schedule.html', {
        'stops':         normalized,
        'train_number':  train_number,
        'data_source':   data_source,
        'page_title':    f'Train {train_number} Schedule — RailTrack India',
    })
