from django.contrib import admin
from .models import SearchHistory


@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display  = ('search_type', 'query', 'data_source', 'timestamp')
    list_filter   = ('search_type', 'data_source')
    search_fields = ('query',)
    ordering      = ('-timestamp',)
