from django.urls import path
from . import views

from apps.accounts.views import ToggleWishlistAPI

app_name = 'catalog'

urlpatterns = [
    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('collection/', views.ProductListView.as_view(), name='collection_alias'),
    path('category/<slug:category_slug>/', views.ProductListView.as_view(), name='category_products'),
    path('products/<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('api/search/', views.SearchAutocompleteAPI.as_view(), name='api_search'),
    path('api/quick-view/<slug:slug>/', views.QuickViewAPI.as_view(), name='api_quick_view'),
    path('api/wishlist/toggle/', ToggleWishlistAPI.as_view(), name='api_toggle_wishlist'),
]
