from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('cart/', views.CartDetailView.as_view(), name='cart_detail'),
    path('api/cart/add/', views.AddToCartAPI.as_view(), name='api_add'),
    path('api/cart/update/', views.UpdateCartItemAPI.as_view(), name='api_update'),
    path('api/cart/remove/', views.RemoveCartItemAPI.as_view(), name='api_remove'),
    path('api/cart/drawer/', views.CartDrawerAPI.as_view(), name='api_drawer'),
]
