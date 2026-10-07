"""
circuit_breaker.py
------------------
Configures a single shared pybreaker CircuitBreaker instance used to
wrap all outgoing calls to the external RapidAPI Indian Railways endpoint.

States:
  CLOSED    → Normal operation. Requests flow to the real API.
  OPEN      → Too many failures. Requests are short-circuited immediately
              and routed to the mock fallback client.
  HALF-OPEN → After reset_timeout seconds, one test request is allowed through.
              If it succeeds → CLOSED. If it fails → back to OPEN.
"""

import logging
import pybreaker
from django.conf import settings

logger = logging.getLogger('tracker')


class RailwayAPIBreakerListener(pybreaker.CircuitBreakerListener):
    """Logs every state change of the circuit breaker."""

    def state_change(self, cb, old_state, new_state):
        logger.warning(
            f"[CircuitBreaker] '{cb.name}' changed state: "
            f"{old_state.name} → {new_state.name}"
        )

    def failure(self, cb, exc):
        logger.error(
            f"[CircuitBreaker] '{cb.name}' recorded a failure "
            f"({cb.fail_counter}/{cb.fail_max}): {exc}"
        )

    def success(self, cb):
        logger.info(f"[CircuitBreaker] '{cb.name}' call succeeded.")


# Single shared instance — import this everywhere you need it
railway_breaker = pybreaker.CircuitBreaker(
    fail_max=settings.CIRCUIT_BREAKER_FAIL_MAX,
    reset_timeout=settings.CIRCUIT_BREAKER_RESET_TIMEOUT,
    name='RailwayAPI',
    listeners=[RailwayAPIBreakerListener()],
)
