from django.contrib import admin
from .models import Order, OrderItem, Coupon, ShippingMethod, Shipment


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_name', 'variant_title', 'sku', 'unit_price', 'quantity', 'line_total')


class ShipmentInline(admin.StackedInline):
    model = Shipment
    can_delete = False
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer_name', 'customer_phone', 'total', 'status', 'payment_method', 'payment_status', 'created_at')
    list_filter = ('status', 'payment_status', 'payment_method', 'created_at')
    search_fields = ('order_number', 'customer_name', 'customer_phone', 'customer_email')
    list_editable = ('status', 'payment_status')
    inlines = [OrderItemInline, ShipmentInline]
    readonly_fields = ('order_number', 'subtotal', 'discount_amount', 'shipping_cost', 'total', 'shipping_address_snapshot')


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'discount_value', 'min_order_value', 'used_count', 'max_uses', 'is_active', 'valid_to')
    list_filter = ('discount_type', 'is_active')
    search_fields = ('code', 'description')
    list_editable = ('is_active',)


@admin.register(ShippingMethod)
class ShippingMethodAdmin(admin.ModelAdmin):
    list_display = ('name_ar', 'code', 'delivery_time_ar', 'cost', 'free_threshold', 'is_active')
    list_editable = ('cost', 'free_threshold', 'is_active')


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ('tracking_number', 'order', 'carrier_name', 'current_status', 'estimated_delivery_date')
    list_filter = ('current_status', 'carrier_name')
    search_fields = ('tracking_number', 'order__order_number')
    list_editable = ('current_status',)
