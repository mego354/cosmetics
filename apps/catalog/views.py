from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import View, ListView, DetailView
from django.http import JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib import messages
from decimal import Decimal
from .models import Category, Subcategory, Product, ProductReview, Wishlist, WishlistItem


class ProductListView(View):
    def get(self, request, category_slug=None):
        products = Product.objects.filter(is_active=True).prefetch_related('images', 'variants')
        
        current_category = None
        if category_slug:
            current_category = get_object_or_404(Category, slug=category_slug)
            products = products.filter(category=current_category)

        # Filters
        subcategory_slug = request.GET.get('subcategory')
        if subcategory_slug:
            products = products.filter(subcategory__slug=subcategory_slug)

        ritual = request.GET.get('ritual')
        if ritual and ritual != 'all':
            products = products.filter(ritual_type=ritual)

        skin_type = request.GET.get('skin_type')
        if skin_type and skin_type != 'all':
            products = products.filter(Q(target_skin_type=skin_type) | Q(target_skin_type='all'))

        min_price = request.GET.get('min_price')
        if min_price:
            try:
                products = products.filter(price__gte=Decimal(min_price))
            except Exception:
                pass

        max_price = request.GET.get('max_price')
        if max_price:
            try:
                products = products.filter(price__lte=Decimal(max_price))
            except Exception:
                pass

        express_only = request.GET.get('express_only')
        if express_only in ['1', 'true']:
            products = products.filter(express_shipping_eligible=True)

        q = request.GET.get('q', '').strip()
        if q:
            products = products.filter(
                Q(name_ar__icontains=q) |
                Q(name_en__icontains=q) |
                Q(short_description_ar__icontains=q) |
                Q(description_ar__icontains=q) |
                Q(ingredients_ar__icontains=q) |
                Q(sku__icontains=q)
            )

        # Sorting
        sort_by = request.GET.get('sort', 'curator')
        if sort_by == 'bestsellers':
            products = products.order_by('-is_bestseller', '-reviews_count', '-id')
        elif sort_by == 'price_asc':
            products = products.order_by('price')
        elif sort_by == 'price_desc':
            products = products.order_by('-price')
        elif sort_by == 'rating':
            products = products.order_by('-average_rating', '-reviews_count')
        else: # curator choice default
            products = products.order_by('-is_featured', '-is_bestseller', '-id')

        # Pagination
        paginator = Paginator(products, 12)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        categories = Category.objects.all()
        total_count = products.count()

        context = {
            'products': page_obj,
            'page_obj': page_obj,
            'total_count': total_count,
            'current_category': current_category,
            'categories': categories,
            'selected_ritual': ritual,
            'selected_skin_type': skin_type,
            'selected_sort': sort_by,
            'search_query': q,
            'express_only': express_only,
            'min_price': min_price or '',
            'max_price': max_price or '',
        }

        # Check if AJAX / Fetch request for dynamic filter
        is_ajax = (
            request.headers.get('x-requested-with') == 'XMLHttpRequest' or 
            request.GET.get('ajax') == '1' or
            'application/json' in request.headers.get('accept', '')
        )

        if is_ajax:
            from django.template.loader import render_to_string
            rendered_html = render_to_string('catalog/components/product_grid_items.html', context, request=request)
            return JsonResponse({
                'success': True,
                'html': rendered_html,
                'total_count': total_count,
                'page': page_obj.number,
                'num_pages': paginator.num_pages,
            })

        return render(request, 'catalog/product_list.html', context)


class ProductDetailView(View):
    def get(self, request, slug):
        product = get_object_or_404(
            Product.objects.prefetch_related('images', 'variants', 'reviews'),
            slug=slug,
            is_active=True
        )
        related_products = Product.objects.filter(
            category=product.category,
            is_active=True
        ).exclude(id=product.id)[:4]

        reviews = product.reviews.filter(is_approved=True)

        context = {
            'product': product,
            'images': product.images.all(),
            'variants': product.variants.all(),
            'default_variant': product.variants.filter(is_default=True).first(),
            'reviews': reviews,
            'related_products': related_products,
        }
        return render(request, 'catalog/product_detail.html', context)

    def post(self, request, slug):
        product = get_object_or_404(Product, slug=slug, is_active=True)
        
        # Add Review Form Submission
        author_name = request.POST.get('author_name', '').strip()
        governorate = request.POST.get('governorate', 'القاهرة')
        rating = request.POST.get('rating', '5')
        title = request.POST.get('title', '').strip()
        comment = request.POST.get('comment', '').strip()

        if author_name and comment:
            try:
                rating_int = min(5, max(1, int(rating)))
            except ValueError:
                rating_int = 5

            ProductReview.objects.create(
                product=product,
                user=request.user if request.user.is_authenticated else None,
                author_name=author_name,
                governorate=governorate,
                rating=rating_int,
                title=title,
                comment=comment,
                is_verified_purchase=True,
                is_approved=True,
            )
            # Update average rating and reviews count
            all_reviews = product.reviews.filter(is_approved=True)
            avg = sum(r.rating for r in all_reviews) / len(all_reviews) if all_reviews else 5.0
            product.average_rating = Decimal(str(round(avg, 2)))
            product.reviews_count = all_reviews.count()
            product.save(update_fields=['average_rating', 'reviews_count'])

            messages.success(request, 'شكراً لمشاركتكِ تجربتكِ الملكية! تم توثيق تقييمكِ بنجاح.')
        else:
            messages.error(request, 'يرجى كتابة اسمكِ وتفاصيل التجربة لإتمام التقييم.')

        return redirect('catalog:product_detail', slug=slug)


class SearchAutocompleteAPI(View):
    def get(self, request):
        q = request.GET.get('q', '').strip()
        if not q or len(q) < 2:
            return JsonResponse({'results': []})

        matches = Product.objects.filter(
            Q(name_ar__icontains=q) |
            Q(name_en__icontains=q) |
            Q(category__name_ar__icontains=q) |
            Q(ingredients_ar__icontains=q),
            is_active=True
        ).prefetch_related('images')[:6]

        results = []
        for p in matches:
            img = p.primary_image
            results.append({
                'id': p.id,
                'name_ar': p.name_ar,
                'name_en': p.name_en,
                'category_name': p.category.name_ar,
                'price': str(p.price),
                'compare_at_price': str(p.compare_at_price) if p.compare_at_price else None,
                'image_url': img.image if img else '',
                'url': f"/products/{p.slug}/",
            })

        return JsonResponse({'results': results})


class QuickViewAPI(View):
    def get(self, request, slug):
        product = get_object_or_404(Product.objects.prefetch_related('images', 'variants'), slug=slug, is_active=True)
        img = product.primary_image
        variants = [{'id': v.id, 'title_ar': v.title_ar, 'price': str(v.price), 'sku': v.sku} for v in product.variants.all()]
        
        return JsonResponse({
            'id': product.id,
            'name_ar': product.name_ar,
            'name_en': product.name_en,
            'category': product.category.name_ar,
            'price': str(product.price),
            'compare_at_price': str(product.compare_at_price) if product.compare_at_price else None,
            'saving': str(product.discount_amount) if product.has_discount else None,
            'short_desc': product.short_description_ar,
            'image_url': img.image if img else '',
            'url': f"/products/{product.slug}/",
            'variants': variants,
            'in_stock': product.is_in_stock,
        })
