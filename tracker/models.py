from django.db import models


class SearchHistory(models.Model):
    """Stores every search made by a user for quick re-runs."""

    SEARCH_TYPES = [
        ('PNR',      'PNR Status'),
        ('RUNNING',  'Train Running Status'),
        ('BETWEEN',  'Trains Between Stations'),
        ('SCHEDULE', 'Train Schedule'),
    ]

    search_type = models.CharField(max_length=20, choices=SEARCH_TYPES)
    # For PNR/RUNNING/SCHEDULE: the number. For BETWEEN: "SRC-DEST"
    query       = models.CharField(max_length=200)
    timestamp   = models.DateTimeField(auto_now_add=True)
    # LIVE_API or MOCK_DATA — tells us which source served the result
    data_source = models.CharField(max_length=20, default='LIVE_API')

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.search_type}] {self.query} @ {self.timestamp:%d %b %Y %H:%M}"
