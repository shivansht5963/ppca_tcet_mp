from django.urls import path
from . import views, api_views

urlpatterns = [

    # ── Django Template Views (UI) ────────────────────────────
    path('',                views.dashboard,      name='dashboard'),
    path('pnr/',            views.pnr_status,     name='pnr_status'),
    path('train/status/',   views.train_status,   name='train_status'),
    path('trains/between/', views.trains_between, name='trains_between'),
    path('train/schedule/', views.train_schedule, name='train_schedule'),

    # ── DRF REST API Endpoints ────────────────────────────────
    # PNR Status:            GET /api/pnr/1234567890/
    path('api/pnr/<str:pnr>/',
         api_views.PNRStatusAPIView.as_view(),
         name='api_pnr_status'),

    # Train Running Status:  GET /api/train/12951/status/
    path('api/train/<str:train_number>/status/',
         api_views.TrainStatusAPIView.as_view(),
         name='api_train_status'),

    # Trains Between:        GET /api/trains/between/NDLS/MMCT/
    path('api/trains/between/<str:from_station>/<str:to_station>/',
         api_views.TrainsBetweenAPIView.as_view(),
         name='api_trains_between'),

    # Train Schedule:        GET /api/train/12951/schedule/
    path('api/train/<str:train_number>/schedule/',
         api_views.TrainScheduleAPIView.as_view(),
         name='api_train_schedule'),

    # Search History:        GET /api/history/
    path('api/history/',
         api_views.SearchHistoryAPIView.as_view(),
         name='api_search_history'),
]
