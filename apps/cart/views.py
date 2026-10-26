from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import View
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.template.loader import render_to_string
from decimal import Decimal
import json
from .models import Cart, CartItem
from apps.catalog.models import Product, ProductVariant


def get_or_create_cart(request):
    """Retrieves or initializes user or guest cart idempotently."""
    if not request.session.session_key:
        request.session.create()
    
    session_key = request.session.session_key

    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        # Migrate guest cart items if any
        if session_key:
            guest_cart = Cart.objects.filter(session_key=session_key).exclude(id=cart.id).first()
            if guest_cart:
                for item in guest_cart.items.all():
                    existing = cart.items.filter(product=item.product, variant=item.variant).first()
                    if existing:
                        existing.quantity += item.quantity
                        existing.save()
                    else:
                        item.cart = cart
                        item.save()
                guest_cart.delete()
    else:
        cart, created = Cart.objects.get_or_create(session_key=session_key)

    return cart


class CartDetailView(View):
    def get(self, request):
        cart = get_or_create_cart(request)
        # Recommended editor add-ons
        addons = Product.objects.filter(
            slug__in=['pocket-travel-scent-mist-10ml', 'organic-egyptian-cotton-cleansing-pads'],
            is_active=True
        )

        context = {
            'cart': cart,
            'items': cart.items.select_related('product', 'variant').all(),
            'addons': addons,
        }
        return render(request, 'cart/cart_detail.html', context)


class AddToCartAPI(View):
    def post(self, request):
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST

            product_id = data.get('product_id')
            variant_id = data.get('variant_id')
            quantity = int(data.get('quantity', 1))

            from apps.core.utils import get_localized_str, get_current_lang
            is_arabic = get_current_lang(request) == 'ar'

            if quantity < 1:
                return JsonResponse({
                    'success': False, 
                    'message': get_localized_str(request, 'الكمية يجب أن تكون 1 على الأقل.', 'Quantity must be at least 1.')
                }, status=400)

            product = get_object_or_404(Product, id=product_id, is_active=True)
            variant = None
            if variant_id:
                variant = get_object_or_404(ProductVariant, id=variant_id, product=product)

            # Stock check
            available_stock = variant.stock if variant else product.stock
            if available_stock < quantity:
                return JsonResponse({
                    'success': False,
                    'message': get_localized_str(
                        request,
                        f'عذراً، الكمية المتوفرة بالمخزن هي {available_stock} فقط.',
                        f'Sorry, only {available_stock} items available in stock.'
                    )
                }, status=400)

            cart = get_or_create_cart(request)
            unit_price = variant.price if variant else product.price

            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                variant=variant,
                defaults={'quantity': quantity, 'price_at_addition': unit_price}
            )

            if not created:
                if cart_item.quantity + quantity > available_stock:
                    return JsonResponse({
                        'success': False,
                        'message': get_localized_str(
                            request,
                            f'لا يمكن إضافة المزيد. المخزون المتاح بالمعمل هو {available_stock} قطعة.',
                            f'Cannot add more. Laboratory stock is limited to {available_stock} pieces.'
                        )
                    }, status=400)
                cart_item.quantity += quantity
                cart_item.save()

            drawer_html = render_to_string('components/cart_drawer_items.html', {'cart': cart}, request=request)
            prod_title = product.name_ar if is_arabic else (product.name_en or product.name_ar)

            return JsonResponse({
                'success': True,
                'message': get_localized_str(
                    request,
                    f'تمت إضافة "{prod_title}" لحقيبة المقتنيات بنجاح.',
                    f'Added "{prod_title}" to your shopping bag.'
                ),
                'total_items': cart.total_items,
                'subtotal': str(cart.subtotal),
                'remaining_free_shipping': str(cart.remaining_for_free_shipping),
                'free_shipping_progress': cart.free_shipping_progress_pct,
                'drawer_html': drawer_html,
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)


class UpdateCartItemAPI(View):
    def post(self, request):
        try:
            from apps.core.utils import get_localized_str
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST

            item_id = data.get('item_id')
            quantity = int(data.get('quantity', 1))

            cart = get_or_create_cart(request)
            cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)

            if quantity <= 0:
                cart_item.delete()
                line_total = Decimal('0.00')
            else:
                available_stock = cart_item.variant.stock if cart_item.variant else cart_item.product.stock
                if quantity > available_stock:
                    return JsonResponse({
                        'success': False,
                        'message': get_localized_str(
                            request,
                            f'الحد الأقصى المتاح بالمخزن هو {available_stock} قطعة.',
                            f'Maximum available stock is {available_stock} pieces.'
                        )
                    }, status=400)
                cart_item.quantity = quantity
                cart_item.save()
                line_total = cart_item.line_total

            drawer_html = render_to_string('components/cart_drawer_items.html', {'cart': cart}, request=request)

            return JsonResponse({
                'success': True,
                'total_items': cart.total_items,
                'subtotal': str(cart.subtotal),
                'line_total': str(line_total),
                'remaining_free_shipping': str(cart.remaining_for_free_shipping),
                'free_shipping_progress': cart.free_shipping_progress_pct,
                'drawer_html': drawer_html,
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)


class RemoveCartItemAPI(View):
    def post(self, request):
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST

            item_id = data.get('item_id')
            cart = get_or_create_cart(request)
            CartItem.objects.filter(id=item_id, cart=cart).delete()

            drawer_html = render_to_string('components/cart_drawer_items.html', {'cart': cart}, request=request)

            return JsonResponse({
                'success': True,
                'total_items': cart.total_items,
                'subtotal': str(cart.subtotal),
                'remaining_free_shipping': str(cart.remaining_for_free_shipping),
                'free_shipping_progress': cart.free_shipping_progress_pct,
                'drawer_html': drawer_html,
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)


class CartDrawerAPI(View):
    def get(self, request):
        cart = get_or_create_cart(request)
        drawer_html = render_to_string('components/cart_drawer_items.html', {'cart': cart}, request=request)
        return JsonResponse({
            'success': True,
            'total_items': cart.total_items,
            'subtotal': str(cart.subtotal),
            'remaining_free_shipping': str(cart.remaining_for_free_shipping),
            'free_shipping_progress': cart.free_shipping_progress_pct,
            'drawer_html': drawer_html,
        })
