from django.contrib import admin
from .models import Category, Subcategory, Brand, Product, ProductImage, ProductVariant, ProductReview, Wishlist, WishlistItem


class SubcategoryInline(admin.TabularInline):
    model = Subcategory
    extra = 1
    prepopulated_fields = {'slug': ('name_en',)}


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('volume_number', 'name_ar', 'name_en', 'french_subtitle', 'is_featured', 'sort_order')
    list_editable = ('is_featured', 'sort_order')
    prepopulated_fields = {'slug': ('name_en',)}
    inlines = [SubcategoryInline]


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name_ar', 'name_en', 'slug')
    prepopulated_fields = {'slug': ('name_en',)}


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name_ar', 'category', 'price', 'compare_at_price', 'stock', 'is_bestseller', 'is_featured', 'is_active', 'average_rating')
    list_filter = ('category', 'ritual_type', 'target_skin_type', 'is_active', 'is_bestseller', 'is_featured')
    search_fields = ('name_ar', 'name_en', 'sku', 'ingredients_ar')
    prepopulated_fields = {'slug': ('name_en',)}
    list_editable = ('price', 'stock', 'is_bestseller', 'is_featured', 'is_active')
    inlines = [ProductImageInline, ProductVariantInline]


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'author_name', 'governorate', 'rating', 'is_verified_purchase', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_verified_purchase', 'is_approved', 'created_at')
    search_fields = ('author_name', 'title', 'comment', 'product__name_ar')
    list_editable = ('is_approved',)
