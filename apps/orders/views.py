from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import View
from django.http import JsonResponse
from django.db import transaction
from django.contrib import messages
from decimal import Decimal
import json
import uuid
from .models import Order, OrderItem, Coupon, ShippingMethod, Shipment
from apps.accounts.models import Address
from apps.cart.views import get_or_create_cart
from apps.catalog.models import Product, ProductVariant


class CheckoutView(View):
    def get(self, request):
        cart = get_or_create_cart(request)
        if cart.items.count() == 0:
            from apps.core.utils import get_localized_str
            messages.warning(
                request,
                get_localized_str(request, 'حقيبة المقتنيات فارغة. يرجى اختيار مستحضراتكِ أولاً.', 'Your shopping bag is empty. Please select artifacts first.')
            )
            return redirect('catalog:product_list')

        if request.user.is_authenticated:
            saved_addresses = Address.objects.filter(user=request.user)
            default_address = saved_addresses.filter(is_default=True).first() or saved_addresses.first()
        else:
            saved_addresses = Address.objects.none()
            default_address = None

        shipping_methods = ShippingMethod.objects.filter(is_active=True)

        # Default shipping calculation
        subtotal = cart.subtotal
        default_shipping = shipping_methods.first()
        shipping_cost = default_shipping.get_effective_cost(subtotal) if default_shipping else Decimal('0.00')
        total = subtotal + shipping_cost

        context = {
            'cart': cart,
            'items': cart.items.select_related('product', 'variant').all(),
            'saved_addresses': saved_addresses,
            'default_address': default_address,
            'shipping_methods': shipping_methods,
            'subtotal': subtotal,
            'shipping_cost': shipping_cost,
            'total': total,
            'governorates': Address.GOVERNORATE_CHOICES,
        }
        return render(request, 'orders/checkout.html', context)

    def post(self, request):
        if not request.session.session_key:
            request.session.save()
        cart = get_or_create_cart(request)
        if cart.items.count() == 0:
            return redirect('catalog:product_list')

        # Form fields
        customer_name = request.POST.get('customer_name', '').strip()
        customer_email = request.POST.get('customer_email', '').strip()
        customer_phone = request.POST.get('customer_phone', '').strip()
        
        governorate = request.POST.get('governorate', 'cairo')
        city = request.POST.get('city', '').strip()
        street_address = request.POST.get('street_address', '').strip()
        building_number = request.POST.get('building_number', '').strip()
        floor_number = request.POST.get('floor_number', '').strip()
        apartment_number = request.POST.get('apartment_number', '').strip()
        nearest_landmark = request.POST.get('nearest_landmark', '').strip()
        
        payment_method = request.POST.get('payment_method', 'cod')
        coupon_code = request.POST.get('coupon_code', '').strip().upper()
        customer_notes = request.POST.get('customer_notes', '').strip()
        whatsapp_opt_in = request.POST.get('whatsapp_opt_in') == 'on'

        # Validation
        from apps.core.utils import get_localized_str
        if not customer_name or not customer_phone or not city or not street_address:
            messages.error(
                request,
                get_localized_str(request, 'يرجى استكمال جميع بيانات العنوان ورقم الهاتف للتوصيل.', 'Please complete all address details and contact phone number for delivery.')
            )
            return redirect('orders:checkout')

        # Calculate everything server-side
        subtotal = cart.subtotal

        # Coupon calculation
        coupon = None
        discount_amount = Decimal('0.00')
        if coupon_code:
            coupon = Coupon.objects.filter(code=coupon_code, is_active=True).first()
            if coupon and coupon.is_valid_now():
                discount_amount = coupon.calculate_discount(subtotal)

        # Shipping method
        shipping_method = ShippingMethod.objects.filter(is_active=True).first()
        shipping_cost = shipping_method.get_effective_cost(subtotal) if shipping_method else Decimal('0.00')

        # 14% VAT is included in standard Egyptian luxury prices
        vat_amount = round((subtotal - discount_amount) * Decimal('0.14') / Decimal('1.14'), 2)
        total = max(Decimal('0.00'), subtotal - discount_amount + shipping_cost)

        with transaction.atomic():
            # Check stock
            for item in cart.items.select_related('product', 'variant'):
                stock_avail = item.variant.stock if item.variant else item.product.stock
                if item.quantity > stock_avail:
                    from apps.core.utils import get_current_lang
                    is_arabic = get_current_lang(request) == 'ar'
                    item_name = item.product.name_ar if is_arabic else (item.product.name_en or item.product.name_ar)
                    messages.error(
                        request,
                        get_localized_str(
                            request,
                            f'عذراً، الكمية المطلوبة من "{item_name}" تجاوزت المخزون المتاح ({stock_avail}).',
                            f'Sorry, the requested quantity for "{item_name}" exceeds available stock ({stock_avail}).'
                        )
                    )
                    return redirect('orders:checkout')

            # Save address snapshot
            address_snapshot = {
                'full_name': customer_name,
                'phone_number': customer_phone,
                'governorate': dict(Address.GOVERNORATE_CHOICES).get(governorate, governorate),
                'city': city,
                'street_address': street_address,
                'building_number': building_number,
                'floor_number': floor_number,
                'apartment_number': apartment_number,
                'nearest_landmark': nearest_landmark,
            }

            shipping_address = None
            if request.user.is_authenticated:
                shipping_address = Address.objects.create(
                    user=request.user,
                    full_name=customer_name,
                    phone_number=customer_phone,
                    governorate=governorate,
                    city=city,
                    street_address=street_address,
                    building_number=building_number,
                    floor_number=floor_number,
                    apartment_number=apartment_number,
                    nearest_landmark=nearest_landmark,
                )

            # Generate unique order number
            order_number = Order.generate_order_number()

            order = Order.objects.create(
                order_number=order_number,
                user=request.user if request.user.is_authenticated else None,
                session_key=request.session.session_key or '',
                customer_name=customer_name,
                customer_email=customer_email,
                customer_phone=customer_phone,
                shipping_address=shipping_address,
                shipping_address_snapshot=address_snapshot,
                shipping_method=shipping_method,
                coupon=coupon,
                status='pending' if payment_method == 'cod' else 'payment_pending',
                payment_method=payment_method,
                payment_status='pending',
                subtotal=subtotal,
                discount_amount=discount_amount,
                shipping_cost=shipping_cost,
                vat_amount=vat_amount,
                total=total,
                currency='EGP',
                whatsapp_opt_in=whatsapp_opt_in,
                customer_notes=customer_notes,
            )

            # Order items & Inventory deduction
            for item in cart.items.select_related('product', 'variant'):
                unit_price = item.variant.price if item.variant else item.product.price
                line_total = unit_price * item.quantity
                img = item.product.primary_image

                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    variant=item.variant,
                    product_name=item.product.name_ar,
                    variant_title=item.variant.title_ar if item.variant else '',
                    sku=item.variant.sku if item.variant else item.product.sku,
                    unit_price=unit_price,
                    quantity=item.quantity,
                    line_total=line_total,
                    product_image_url=img.image if img else '',
                )

                # Deduct stock
                if item.variant:
                    item.variant.stock = max(0, item.variant.stock - item.quantity)
                    item.variant.save(update_fields=['stock'])
                else:
                    item.product.stock = max(0, item.product.stock - item.quantity)
                    item.product.save(update_fields=['stock'])

            # Increment coupon usage
            if coupon:
                coupon.used_count += 1
                coupon.save(update_fields=['used_count'])

            # Create shipment record
            tracking_num = f"LME-TRK-{uuid.uuid4().hex[:8].upper()}"
            Shipment.objects.create(
                order=order,
                tracking_number=tracking_num,
                current_status='preparing',
                status_history=[{
                    'status': 'preparing',
                    'note': 'تم تسجيل الطلب وجاري تجهيز التغليف الملكي بختم الشمع',
                    'timestamp': order.created_at.isoformat()
                }]
            )

            # Clear cart
            cart.items.all().delete()
            request.session['last_order_number'] = order.order_number

        # Route according to payment method
        from apps.core.utils import get_localized_str
        if payment_method == 'paymob_card':
            return redirect('payments:paymob_initiate', order_number=order.order_number)
        else:
            msg = get_localized_str(
                request,
                f'تم تأكيد طلبكِ بنجاح! رقم الطلب: {order.order_number}',
                f'Your royal order #{order.order_number} has been confirmed successfully!'
            )
            messages.success(request, msg)
            return redirect('orders:confirmation', order_number=order.order_number)


class ValidateCouponAPI(View):
    def post(self, request):
        from apps.core.utils import get_localized_str
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            code = data.get('code', '').strip().upper()
            
            cart = get_or_create_cart(request)
            subtotal = cart.subtotal

            coupon = Coupon.objects.filter(code=code, is_active=True).first()
            if not coupon:
                return JsonResponse({
                    'valid': False, 
                    'message': get_localized_str(request, 'رمز القسيمة غير صحيح أو غير متاح حالياً.', 'Invalid or unavailable promotion code.')
                })

            if not coupon.is_valid_now():
                return JsonResponse({
                    'valid': False, 
                    'message': get_localized_str(request, 'هذه القسيمة منتهية الصلاحية أو استنفذت عدد الاستخدامات.', 'This coupon code has expired or reached usage limits.')
                })

            if subtotal < coupon.min_order_value:
                return JsonResponse({
                    'valid': False,
                    'message': get_localized_str(
                        request,
                        f'الحد الأدنى لتفعيل هذا الكود هو {coupon.min_order_value} ج.م.',
                        f'Minimum order value for this coupon is {coupon.min_order_value} EGP.'
                    )
                })

            discount = coupon.calculate_discount(subtotal)
            new_total = max(Decimal('0.00'), subtotal - discount)
            currency_txt = get_localized_str(request, 'ج.م', 'EGP')

            return JsonResponse({
                'valid': True,
                'discount_amount': str(discount),
                'new_total': str(new_total),
                'message': get_localized_str(
                    request,
                    f'تم تفعيل خصم {coupon.discount_value}{"%" if coupon.discount_type == "percentage" else " ج.م"} بنجاح! وفرتِ {discount} ج.م',
                    f'Promotion code applied successfully! Saved {discount} EGP'
                ),
            })
        except Exception as e:
            return JsonResponse({'valid': False, 'message': str(e)}, status=500)


class OrderConfirmationView(View):
    def get(self, request, order_number):
        from apps.core.utils import get_localized_str
        order = get_object_or_404(
            Order.objects.prefetch_related('items', 'shipment'),
            order_number=order_number
        )
        
        # IDOR Protection: The placing customer, current session owner, or guest with the order URL can view
        is_owner = False
        if request.user.is_authenticated and order.user == request.user:
            is_owner = True
        elif request.session.get('last_order_number') == order.order_number:
            is_owner = True
        elif order.session_key and request.session.session_key == order.session_key:
            is_owner = True
        elif not order.user:
            is_owner = True

        if not is_owner and not request.user.is_staff:
            messages.error(request, get_localized_str(request, 'غير مصرح لكِ بالوصول إلى هذا الطلب.', 'You are not authorized to view this order.'))
            return redirect('core:home')

        return render(request, 'orders/order_confirmation.html', {'order': order})


class OrderTrackView(View):
    def get(self, request, tracking_number=None):
        from apps.core.utils import get_localized_str
        order = None
        shipment = None
        query = tracking_number or request.GET.get('q', '').strip()
        auth_error = False

        if query:
            # Query by tracking number or order number
            shipment = Shipment.objects.filter(tracking_number=query).select_related('order').first()
            if not shipment:
                order = Order.objects.filter(order_number=query).prefetch_related('shipment', 'items').first()
                if order and hasattr(order, 'shipment'):
                    shipment = order.shipment
            else:
                order = shipment.order

            if order:
                # IDOR Check: Authenticated user must own the order, or session must match, or verify_phone must match
                is_authorized = False
                if request.user.is_authenticated and order.user == request.user:
                    is_authorized = True
                elif request.session.get('last_order_number') == order.order_number:
                    is_authorized = True
                elif order.session_key and request.session.session_key == order.session_key:
                    is_authorized = True
                else:
                    phone_attempt = request.GET.get('phone', '').strip()
                    if phone_attempt and phone_attempt[-6:] in order.customer_phone:
                        is_authorized = True
                    elif request.user.is_staff:
                        is_authorized = True

                if not is_authorized:
                    auth_error = True
                    order = None
                    shipment = None
                    messages.error(
                        request,
                        get_localized_str(
                            request,
                            'لحماية خصوصية العملاء، يرجى إدخال رقم الهاتف المسجل مع كود الطلب لتتبع الشحنة.',
                            'For security, please provide the registered phone number alongside the order number to track this dispatch.'
                        )
                    )

        context = {
            'order': order,
            'shipment': shipment,
            'search_query': query,
            'auth_error': auth_error,
        }
        return render(request, 'orders/order_tracking.html', context)
