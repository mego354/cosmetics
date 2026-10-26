from django.shortcuts import render, redirect
from django.views.generic import View, TemplateView
from django.utils.translation import activate
from django.conf import settings
from apps.catalog.models import Category, Product


class HomeView(View):
    def get(self, request):
        categories = Category.objects.filter(is_featured=True).order_by('sort_order')
        bestsellers = Product.objects.filter(is_active=True, is_bestseller=True).prefetch_related('images', 'variants')[:8]
        featured_products = Product.objects.filter(is_active=True, is_featured=True).prefetch_related('images', 'variants')[:8]
        new_arrivals = Product.objects.filter(is_active=True, is_new_arrival=True).prefetch_related('images', 'variants')[:4]
        
        # Hero product (e.g. Royal Blue Lotus Serum)
        hero_product = Product.objects.filter(slug='royal-blue-lotus-24k-gold-serum').prefetch_related('images', 'variants').first()

        context = {
            'categories': categories,
            'bestsellers': bestsellers,
            'featured_products': featured_products,
            'new_arrivals': new_arrivals,
            'hero_product': hero_product,
        }
        return render(request, 'core/home.html', context)


class SwitchLanguageView(View):
    def get(self, request, lang_code):
        if lang_code in ['ar', 'en']:
            request.session['django_language'] = lang_code
            activate(lang_code)
            if request.user.is_authenticated:
                from apps.accounts.models import CustomerProfile
                CustomerProfile.objects.filter(user=request.user).update(preferred_language=lang_code)
        
        next_url = request.META.get('HTTP_REFERER') or '/'
        response = redirect(next_url)
        cookie_name = getattr(settings, 'LANGUAGE_COOKIE_NAME', 'django_language')
        response.set_cookie(cookie_name, lang_code, max_age=86400 * 365, samesite='Lax')
        return response


class AboutView(TemplateView):
    template_name = 'core/about.html'


class RitualsView(TemplateView):
    template_name = 'core/rituals.html'


class StoriesView(TemplateView):
    template_name = 'core/stories.html'
