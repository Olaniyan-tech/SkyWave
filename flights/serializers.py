from rest_framework import serializers
from datetime import date


class FlightSearchSerializer(serializers.Serializer):
    origin = serializers.CharField(max_length=3, min_length=3)
    destination = serializers.CharField(max_length=3, min_length=3)
    departure_date = serializers.DateField()
    return_date = serializers.DateField(required=False, allow_null=True)
    adults = serializers.IntegerField(min_value=1, max_value=9, default=1)
    cabin_class = serializers.ChoiceField(
        choices=['economy', 'premium_economy', 'business', 'first'],
        default='economy'
    )

    def validate_origin(self, value):
        return value.upper()

    def validate_destination(self, value):
        return value.upper()
    
    def validate_cabin_class(self, value):
        return value.lower()
    
    def validate_departure_date(self, value):
        if value < date.today():
            raise serializers.ValidationError("Departure date cannot be in the past.")
        return value


    def validate(self, data):
        if data['origin'] == data['destination']:
            raise serializers.ValidationError({
                "destination": "Origin and destination cannot be the same."}
            )
        
        if data.get('return_date'):
            if data['return_date'] <= data['departure_date']:
                raise serializers.ValidationError({
                    "return_date": "Return date cannot be before departure date."}
                )

        return data


class AirportSerializer(serializers.Serializer):
    q = serializers.CharField(min_length=2)

    def validate_q(self, value):
        return value.strip()