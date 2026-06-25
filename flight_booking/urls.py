from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def api_home(request):
    return JsonResponse({
        "message": "Welcome to SkyWave!",
        "status": "API is running"
    })

urlpatterns = [
    path('', api_home),
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),
    path('api/flights/', include('flights.urls')),  
    path('api/bookings/', include('bookings.urls')),
    path('api/payments/', include('payments.urls')),
]
