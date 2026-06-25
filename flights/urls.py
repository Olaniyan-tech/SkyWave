from django.urls import path
from bookings import views
from flights.views import FlightSearchView, FlightOfferDetailView, AirportSearchView


urlpatterns = [
    path('search/', FlightSearchView.as_view(), name='flight-search'),
    path('offers/<str:offer_id>/', FlightOfferDetailView.as_view(), name='flight-offer-detail'),
    path('airports/', AirportSearchView.as_view(), name='airport-search'),
]