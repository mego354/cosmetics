from decimal import Decimal
from django.conf import settings
from apps.catalog.models import Category, Wishlist
from apps.cart.models import Cart
from apps.accounts.models import Address


def global_context(request):
    # Language & Direction: Default is Arabic ('ar')
    lang = request.session.get('django_language') or request.COOKIES.get(getattr(settings, 'LANGUAGE_COOKIE_NAME', 'django_language'), 'ar')
    if lang not in ['ar', 'en']:
        lang = 'ar'

    is_ar = (lang == 'ar')
    is_en = (lang == 'en')
    is_rtl = is_ar
    currency_symbol = 'ج.م' if is_ar else 'EGP'
    
    # Categories for navigation
    categories = Category.objects.prefetch_related('subcategories').all()
    
    # Wishlist count
    wishlist_count = 0
    if request.user.is_authenticated:
        wishlist = Wishlist.objects.filter(user=request.user).first()
    else:
        session_key = request.session.session_key
        wishlist = Wishlist.objects.filter(session_key=session_key).first() if session_key else None
        
    if wishlist:
        wishlist_count = wishlist.items.count()

    # Cart snapshot for header
    cart_count = 0
    cart_subtotal = Decimal('0.00')
    cart_qualifies_free_shipping = False
    cart_remaining_free_shipping = Decimal('800.00')
    cart_free_shipping_progress = 0
    cart_qualifies_gift = False
    cart_remaining_gift = Decimal('1200.00')
    cart_gift_progress = 0
    
    cart = None
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
    elif request.session.session_key:
        cart = Cart.objects.filter(session_key=request.session.session_key).first()

    if cart:
        cart_count = cart.total_items
        cart_subtotal = cart.subtotal
        cart_qualifies_free_shipping = cart.qualifies_for_free_shipping
        cart_remaining_free_shipping = cart.remaining_for_free_shipping
        cart_free_shipping_progress = cart.free_shipping_progress_pct
        cart_qualifies_gift = cart.qualifies_for_complimentary_gift
        cart_remaining_gift = cart.remaining_for_complimentary_gift
        cart_gift_progress = cart.gift_progress_pct

    return {
        'nav_categories': categories,
        'current_language': lang,
        'is_ar': is_ar,
        'is_en': is_en,
        'is_rtl': is_rtl,
        'currency_symbol': currency_symbol,
        'wishlist_count': wishlist_count,
        'cart_count': cart_count,
        'cart_subtotal': cart_subtotal,
        'cart_obj': cart,
        'cart_qualifies_free_shipping': cart_qualifies_free_shipping,
        'cart_remaining_free_shipping': cart_remaining_free_shipping,
        'cart_free_shipping_progress': cart_free_shipping_progress,
        'cart_qualifies_gift': cart_qualifies_gift,
        'cart_remaining_gift': cart_remaining_gift,
        'cart_gift_progress': cart_gift_progress,
        'egyptian_governorates': Address.GOVERNORATE_CHOICES,
    }
