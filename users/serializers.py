from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from users.validators import validate_phone_format
from django.db import transaction

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    phone = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)


    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'phone', 'password', 'confirm_password']
        read_only_fields = ['id']

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("This email is already in use.")    
        return value.lower()
    
    def validate_phone(self, value):
        validate_phone_format(value)
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("This phone number is already in use.")
        return value
    

    def validate_password(self, value):
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value
    
    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Password do not match."})
        return data
    
    
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        with transaction.atomic():
            user = User.objects.create_user(**validated_data)
            return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'phone', 'first_name', 'last_name', 'created_at']
        read_only_fields = ['id', 'email', 'created_at']


class RequestPasswordResetSerializer(serializers.Serializer):
    # User sends their email to request a password reset.
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        return value.lower().strip()


class ConfirmPasswordResetSerializer(serializers.Serializer):
    # User sends their new password along with the token to reset their password.

    token = serializers.CharField(required=True)
    new_password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    def validate_token(self, value):
        if not value.strip():
            raise serializers.ValidationError("Token cannot be blank.")
        return value.strip()

    def validate_new_password(self, value):
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match."}
            )
        return data