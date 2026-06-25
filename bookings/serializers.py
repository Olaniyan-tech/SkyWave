from rest_framework import serializers
from django.utils import timezone
from django.db import transaction
from bookings.models import Booking, Passenger



class PassengerSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Passenger
        fields = [
            'id', 'full_name', 'title', 'first_name', 'last_name',
            'gender', 'date_of_birth', 'passenger_type',
            'passport_number', 'passport_expiry',
            'nationality', 'email', 'phone_number',
        ]
        read_only_fields = ['id', 'full_name']

    def get_full_name(self, obj):
        return obj.full_name
    
    def validate_passport_expiry(self, value):
        if value <= timezone.now().date():
            raise serializers.ValidationError(
                "Passport has expired. Please provide a valid passport."
            )
        return value
    
    def validate_date_of_birth(self, value):
        if value >= timezone.now().date():
            raise serializers.ValidationError(
                "Date of birth cannot be today or in the future. Please provide a valid date of birth."
            )
        return value
    
    def validate_first_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("First name cannot be blank.")
        return value.strip()
    
    def validate_last_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Last name cannot be blank.")
        return value.strip()

class BookingCreateSerializer(serializers.Serializer):
    offer_id = serializers.CharField(required=True)
    passengers = PassengerSerializer(many=True, required=True)

    def validate_offer_id(self, value):
        if not value.strip():
            raise serializers.ValidationError("Offer ID cannot be blank.")
        return value.strip()
    
    def validate_passengers(self, value):
        if len(value) == 0:
            raise serializers.ValidationError("At least one passenger is required.")
        if len(value) > 9:
            raise serializers.ValidationError("A maximum of 9 passengers is allowed per booking.")
        return value


class BookingListSerializer(serializers.ModelSerializer):
    passenger_count = serializers.IntegerField(source='passengers.count', read_only=True)
    is_cancellable = serializers.BooleanField(read_only=True)
    flight_duration = serializers.CharField(read_only=True, allow_null=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'booking_reference', 'origin_airport', 'destination_airport',
            'departure_time', 'arrival_time', 'flight_duration', 'trip_type', 
            'cabin_class', 'airline_name', 'airline_iata_code', 'flight_number',
            'total_amount', 'currency', 'booking_status', 'payment_status',
            'passenger_count', 'is_cancellable', 'created_at',
        ]
        read_only_fields = [
            'id', 'booking_reference', 'origin_airport', 'destination_airport',
            'departure_time', 'arrival_time', 'flight_duration', 'trip_type', 
            'cabin_class', 'airline_name', 'airline_iata_code', 'flight_number',
            'total_amount', 'currency', 'booking_status', 'payment_status',
            'passenger_count', 'is_cancellable', 'created_at',
        ]


class BookingDetailSerializer(serializers.ModelSerializer):
    passengers = PassengerSerializer(many=True, read_only=True)
    passenger_count = serializers.IntegerField(source='passengers.count', read_only=True)
    is_cancellable = serializers.BooleanField(read_only=True)
    flight_duration = serializers.CharField(read_only=True, allow_null=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'booking_reference', 'offer_id', 'duffel_order_id',
            'trip_type', 'origin_airport', 'destination_airport', 'departure_time', 
            'arrival_time', 'flight_duration', 'return_departure_time', 'return_arrival_time',
            'airline_name', 'airline_iata_code', 'flight_number', 'cabin_class',
            'base_amount', 'tax_amount', 'total_amount', 'currency',
            'baggage_allowance', 'booking_status', 'payment_status', 'passengers', 
            'passenger_count', 'is_cancellable', 'created_at', 'updated_at',
        ]
        read_only_fields = fields
