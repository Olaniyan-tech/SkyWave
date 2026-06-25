from payments.models import Payment


def get_payment_by_reference(reference):
    try:
        return Payment.objects.select_related(
            "booking", "booking__user"
        ).get(payment_reference=reference)
    except Payment.DoesNotExist:
        return None

def get_payment_by_booking(booking):
    try:
        return Payment.objects.get(booking=booking)
    except Payment.DoesNotExist:
        return None

def get_user_payments(user):
    return Payment.objects.select_related("booking").filter(
        booking__user=user
    ).order_by("-created_at")