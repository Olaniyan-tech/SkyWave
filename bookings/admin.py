from django.contrib import admin
from bookings.models import Passenger, Booking



class PassengerAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'first_name', 'last_name', 'passenger_type', 
        'nationality', 'passport_number', 'email', 'phone_number'
    ]
    list_filter = ['title', 'passenger_type', 'nationality']
    search_fields = ['first_name', 'last_name', 'passport_number', 'email']
    ordering = ['last_name', 'first_name']
admin.site.register(Passenger, PassengerAdmin)

class PassengerInline(admin.TabularInline):
    model = Booking.passengers.through
    extra = 0
    verbose_name = "Passenger"


class BookingAdmin(admin.ModelAdmin):
    list_display = [
        'booking_reference', 'user', 'origin_airport', 'destination_airport', 
        'trip_type', 'cabin_class', 'total_amount', 'currency', 'booking_status', 
        'payment_status', 'created_at'
    ]
    list_filter = ['booking_status', 'payment_status', 'cabin_class', 'trip_type']
    search_fields = [
        'booking_reference', 'user__email', 'origin_airport',
        'destination_airport', 'flight_number']
    ordering = ['-created_at']
    readonly_fields = ['booking_reference', 'flight_duration', 'passenger_count', 'created_at', 'updated_at']
    inlines = [PassengerInline]


    fieldsets = (
        ('Reference', {'fields': ('booking_reference', 'user', 'offer_id', 'duffel_order_id')}),
        ('Trip', {'fields': ('trip_type', 'cabin_class', 'origin_airport', 'destination_airport')}),
        ('Outbound Flight', {'fields': ('departure_time', 'arrival_time', 'flight_duration')}),
        ('Return Flight', {'fields': ('return_departure_time', 'return_arrival_time')}),
        ('Airline', {'fields': ('airline_name', 'airline_iata_code', 'flight_number')}),
        ('Pricing', {'fields': ('base_amount', 'tax_amount', 'total_amount', 'currency')}),
        ('Baggage', {'fields': ('baggage_allowance',)}),
        ('Status', {'fields': ('booking_status', 'payment_status')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )

admin.site.register(Booking, BookingAdmin)