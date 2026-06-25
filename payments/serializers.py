from rest_framework import serializers
from payments.models import Payment


class PaymentInitializeSerializer(serializers.Serializer):
    booking_reference = serializers.CharField(required=True)

    def validate_booking_reference(self, value):
        if not value.strip():
            raise serializers.ValidationError("Booking reference cannot be empty.")
        return value.strip().upper()
    

class PaymentDetailSerializer(serializers.ModelSerializer):
    booking_reference = serializers.CharField(source="booking.booking_reference", read_only=True)
    origin = serializers.CharField(source="booking.origin_airport", read_only=True)
    destination = serializers.CharField(source="booking.destination_airport", read_only=True)
    airline = serializers.CharField(source="booking.airline_name", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id", "booking_reference", "origin", "destination", "airline",
            "payment_reference", "paystack_reference", "amount", "currency", 
            "payment_status", "payment_method", "channel", "card_last_four", 
            "card_brand", "paid_at", "created_at", "updated_at"
        ]
        read_only_fields = [
            "id", "booking_reference", "origin", "destination", "airline",
            "payment_reference", "paystack_reference", "amount", "currency", 
            "payment_status", "payment_method", "channel", "card_last_four", 
            "card_brand", "paid_at", "created_at", "updated_at"
        ]