from django.contrib import admin
from .models import Payment


class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'payment_reference', 'booking', 'amount', 'currency',
        'payment_status', 'payment_method', 'channel',
        'card_brand', 'card_last_four', 'paid_at', 'created_at',
    ]
    list_filter  = ['payment_status', 'payment_method', 'currency', 'card_brand']
    search_fields = [
        'payment_reference', 'paystack_reference',
        'booking__booking_reference', 'booking__user__email',
    ]
    ordering      = ['-created_at']
    readonly_fields = [
        'id', 'payment_reference', 'paystack_reference',
        'paystack_response', 'paid_at', 'created_at', 'updated_at',
    ]

    fieldsets = (
        ('References', {'fields': ('id', 'booking', 'payment_reference', 'paystack_reference')}),
        ('Amount',     {'fields': ('amount', 'currency')}),
        ('Status',     {'fields': ('payment_status', 'payment_method', 'channel')}),
        ('Card Info',  {'fields': ('card_last_four', 'card_brand')}),
        ('Paystack',   {'fields': ('paystack_response',)}),
        ('Timestamps', {'fields': ('paid_at', 'created_at', 'updated_at')}),
    )

admin.site.register(Payment, PaymentAdmin)