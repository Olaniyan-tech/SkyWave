from django.urls import path
from .views import (
    BookingCreateView,
    BookingListView,
    BookingDetailView,
    BookingCancelView,
    BookingStatsView,
)

urlpatterns = [
    path('create/', BookingCreateView.as_view(), name='booking-create'),
    path('lists/', BookingListView.as_view(), name='booking-list'),
    path('stats/', BookingStatsView.as_view(), name='booking-stats'),
    path('<str:booking_reference>/details/', BookingDetailView.as_view(), name='booking-detail'),
    path('<str:booking_reference>/cancel/', BookingCancelView.as_view(), name='booking-cancel'),
]