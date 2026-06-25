import phonenumbers
from rest_framework import serializers
from django.core.exceptions import ValidationError


def parse_and_validate_phone_number(value):
    try:
        phone = phonenumbers.parse(value)
        if not phonenumbers.is_valid_number(phone):
            return False
    except phonenumbers.NumberParseException:
        return False
    
    return True


def validate_phone_format(value):
    if not parse_and_validate_phone_number(value):
        raise serializers.ValidationError(
            "Enter a valid phone number with country code e.g +2349039624784"
        )



def validate_phone_number(value):
    if not parse_and_validate_phone_number(value):
        raise ValidationError(
            "Enter a valid phone number with country code e.g. +2348012345678"
        )
