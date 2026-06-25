from django.urls import path
from .views import (
    PaymentInitializeView, 
    PaymentVerifyView,
    PaymentDetailView,
    PaymentListView
)


urlpatterns = [
    path('', PaymentListView.as_view(), name='payment-list'),
    path('initialize/', PaymentInitializeView.as_view(), name='payment-initialize'),
    path('verify/', PaymentVerifyView.as_view(), name='payment-verify'),
    path('<str:booking_reference>/', PaymentDetailView.as_view(), name='payment-detail'),
]