from django.db import models
from django.contrib.auth import get_user_model
import uuid
import random
import string

User = get_user_model()


class Passenger(models.Model):
    TITLE_CHOICES = [
        ('MR', 'Mr.'),
        ('MS', 'Ms.'),
        ('MRS', 'Mrs.'),
        ('DR', 'Dr.'),
    ]
    PASSENGER_TYPE_CHOICES = [
        ('ADULT', 'Adult'),
        ('CHILD', 'Child'),
        ('INFANT', 'Infant'),
    ]
    GENDER_CHOICES = [
        ('MALE', 'Male'),
        ('FEMALE', 'Female'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=5, choices=TITLE_CHOICES)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=6, choices=GENDER_CHOICES, default='MALE')
    date_of_birth = models.DateField()
    passenger_type = models.CharField(max_length=10, choices=PASSENGER_TYPE_CHOICES, default='ADULT')
    passport_number = models.CharField(max_length=50)
    passport_expiry = models.DateField()
    nationality = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} {self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Booking(models.Model):
    TRIP_TYPE_CHOICES = [
        ('ONE_WAY', 'One Way'),
        ('ROUND_TRIP', 'Round Trip'),
    ]
    BOOKING_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    PAYMENT_STATUS_CHOICES = [
        ('UNPAID', 'Unpaid'),
        ('PAID', 'Paid'),
        ('REFUNDED', 'Refunded'),
        ('FAILED', 'Failed'),
    ]
    CABIN_CLASS_CHOICES = [
        ('economy', 'Economy'),
        ('premium_economy', 'Premium Economy'),
        ('business', 'Business'),
        ('first', 'First Class'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking_reference = models.CharField(max_length=10, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    passengers = models.ManyToManyField(Passenger, related_name='bookings')

    offer_id = models.CharField(max_length=200)
    duffel_order_id = models.CharField(max_length=200, blank=True)

    trip_type = models.CharField(max_length=20, choices=TRIP_TYPE_CHOICES, default='ONE_WAY')
    origin_airport = models.CharField(max_length=3)
    destination_airport = models.CharField(max_length=3)
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()

    return_departure_time = models.DateTimeField(null=True, blank=True)
    return_arrival_time = models.DateTimeField(null=True, blank=True)


    airline_name = models.CharField(max_length=200)
    airline_iata_code = models.CharField(max_length=3)
    flight_number = models.CharField(max_length=20)
    cabin_class = models.CharField(max_length=20, choices=CABIN_CLASS_CHOICES)

    base_amount = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')

    baggage_allowance = models.JSONField(default=list)

    booking_status = models.CharField(max_length=20, choices=BOOKING_STATUS_CHOICES, default='PENDING')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='UNPAID')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    

    class Meta:
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.booking_reference:
            self.booking_reference = 'BK-' + ''.join(
                random.choices(string.ascii_uppercase + string.digits, k=6)
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Booking {self.booking_reference} - {self.origin_airport} to {self.destination_airport} for {self.user.username} [{self.booking_status}]"
    
    @property
    def passenger_count(self):
        return self.passengers.count()
    
    @property
    def is_cancellable(self):
        return self.booking_status in ('PENDING', 'CONFIRMED')
    
    @property
    def flight_duration(self):
        if self.departure_time and self.arrival_time:
            diff = self.arrival_time - self.departure_time
            total_minutes = int(diff.total_seconds() / 60)
            hours, minutes = divmod(total_minutes, 60)
            return f"{hours}h {minutes}m"
        return None