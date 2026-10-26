from django.contrib import admin
from .models import Payment, Notification


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('order', 'payment_method', 'amount', 'currency', 'status', 'paymob_transaction_id', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('order__order_number', 'paymob_transaction_id', 'paymob_order_id')
    readonly_fields = ('raw_response', 'created_at', 'updated_at')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title_ar', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
