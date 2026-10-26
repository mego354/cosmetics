from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import View
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from decimal import Decimal
import json
from .models import User, CustomerProfile, Address
from apps.orders.models import Order
from apps.catalog.models import Product, Wishlist, WishlistItem


class LoginView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('accounts:dashboard')
        return render(request, 'accounts/login.html')

    def post(self, request):
        username_or_email = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        next_url = request.POST.get('next', '') or request.GET.get('next', '')

        user = authenticate(request, username=username_or_email, password=password)
        if not user:
            # Check if email was provided
            user_by_email = User.objects.filter(email=username_or_email).first()
            if user_by_email:
                user = authenticate(request, username=user_by_email.username, password=password)

        if user:
            login(request, user)
            messages.success(request, f'أهلاً بكِ مجدداً في دار لوميه، {user.first_name or user.username}!')
            return redirect(next_url or 'accounts:dashboard')
        else:
            messages.error(request, 'البريد الإلكتروني أو كلمة المرور غير صحيحة. يرجى المحاولة مرة أخرى.')
            return render(request, 'accounts/login.html')


class RegisterView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('accounts:dashboard')
        return render(request, 'accounts/register.html')

    def post(self, request):
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        phone_number = request.POST.get('phone_number', '').strip()
        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()

        if not full_name or not email or not password:
            messages.error(request, 'يرجى استيفاء جميع الحقول المطلوبة.')
            return render(request, 'accounts/register.html')

        if password != confirm_password:
            messages.error(request, 'كلمة المرور وتأكيد كلمة المرور غير متطابقين.')
            return render(request, 'accounts/register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'هذا البريد الإلكتروني مسجل بالفعل لدينا. يمكنكِ تسجيل الدخول.')
            return render(request, 'accounts/register.html')

        username = email.split('@')[0]
        counter = 1
        base_username = username
        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1

        name_parts = full_name.split()
        first_name = name_parts[0] if name_parts else ''
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ''

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
        )
        CustomerProfile.objects.create(user=user, loyalty_points=100)

        login(request, user)
        messages.success(request, 'تم إنشاء حسابكِ الملكي بنجاح! تم منحكِ 100 نقطة ولاء ترحيبية.')
        return redirect('accounts:dashboard')


class LogoutView(View):
    def get(self, request):
        logout(request)
        messages.info(request, 'تم تسجيل الخروج بنجاح. نراكِ قريباً في دار لوميه.')
        return redirect('core:home')


class AccountDashboardView(LoginRequiredMixin, View):
    def get(self, request):
        recent_orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
        addresses = Address.objects.filter(user=request.user)
        profile, _ = CustomerProfile.objects.get_or_create(user=request.user)
        
        wishlist = Wishlist.objects.filter(user=request.user).first()
        wishlist_count = wishlist.items.count() if wishlist else 0

        context = {
            'user': request.user,
            'profile': profile,
            'recent_orders': recent_orders,
            'addresses': addresses,
            'wishlist_count': wishlist_count,
        }
        return render(request, 'accounts/dashboard.html', context)


class OrderHistoryView(LoginRequiredMixin, View):
    def get(self, request):
        orders = Order.objects.filter(user=request.user).prefetch_related('items', 'shipment').order_by('-created_at')
        return render(request, 'accounts/order_history.html', {'orders': orders})


class AccountOrderDetailView(LoginRequiredMixin, View):
    def get(self, request, order_number):
        order = get_object_or_404(Order.objects.prefetch_related('items', 'shipment'), order_number=order_number, user=request.user)
        return render(request, 'accounts/order_detail.html', {'order': order})


class AddressBookView(LoginRequiredMixin, View):
    def get(self, request):
        addresses = Address.objects.filter(user=request.user)
        return render(request, 'accounts/address_book.html', {
            'addresses': addresses,
            'governorates': Address.GOVERNORATE_CHOICES,
        })

    def post(self, request):
        action = request.POST.get('action')
        address_id = request.POST.get('address_id')

        if action == 'delete' and address_id:
            Address.objects.filter(id=address_id, user=request.user).delete()
            messages.success(request, 'تم حذف العنوان بنجاح.')
        elif action == 'set_default' and address_id:
            addr = get_object_or_404(Address, id=address_id, user=request.user)
            addr.is_default = True
            addr.save()
            messages.success(request, 'تم تعيين العنوان الافتراضي بنجاح.')
        else:
            full_name = request.POST.get('full_name', '').strip()
            phone = request.POST.get('phone_number', '').strip()
            gov = request.POST.get('governorate', 'cairo')
            city = request.POST.get('city', '').strip()
            street = request.POST.get('street_address', '').strip()
            bldg = request.POST.get('building_number', '').strip()
            landmark = request.POST.get('nearest_landmark', '').strip()

            if full_name and phone and city and street:
                Address.objects.create(
                    user=request.user,
                    full_name=full_name,
                    phone_number=phone,
                    governorate=gov,
                    city=city,
                    street_address=street,
                    building_number=bldg,
                    nearest_landmark=landmark,
                    is_default=Address.objects.filter(user=request.user).count() == 0,
                )
                messages.success(request, 'تم حفظ العنوان الجديد بنجاح.')

        return redirect('accounts:addresses')


class WishlistView(View):
    def get(self, request):
        if request.user.is_authenticated:
            wishlist = Wishlist.objects.filter(user=request.user).first()
        else:
            session_key = request.session.session_key
            wishlist = Wishlist.objects.filter(session_key=session_key).first() if session_key else None

        items = wishlist.items.select_related('product', 'variant') if wishlist else []
        return render(request, 'accounts/wishlist.html', {'wishlist_items': items})


class ToggleWishlistAPI(View):
    def post(self, request):
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            product_id = data.get('product_id')

            product = get_object_or_404(Product, id=product_id, is_active=True)

            if not request.session.session_key:
                request.session.create()

            if request.user.is_authenticated:
                wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
            else:
                wishlist, _ = Wishlist.objects.get_or_create(session_key=request.session.session_key)

            from apps.core.utils import get_localized_str
            existing_item = WishlistItem.objects.filter(wishlist=wishlist, product=product).first()
            p_name = product.name_en if get_localized_str(request, 'ar', 'en') == 'en' and product.name_en else product.name_ar

            if existing_item:
                existing_item.delete()
                in_wishlist = False
                msg = get_localized_str(request, f'تمت إزالة "{p_name}" من المفضلة.', f'"{p_name}" removed from royal wishlist.')
            else:
                WishlistItem.objects.create(wishlist=wishlist, product=product)
                in_wishlist = True
                msg = get_localized_str(request, f'تمت إضافة "{p_name}" إلى قائمة مقتنياتكِ المفضلة.', f'"{p_name}" added to your royal wishlist.')

            return JsonResponse({
                'success': True,
                'in_wishlist': in_wishlist,
                'wishlist_count': wishlist.items.count(),
                'message': msg,
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
