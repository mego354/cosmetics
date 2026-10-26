from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('dashboard/', views.AccountDashboardView.as_view(), name='dashboard'),
    path('orders/', views.OrderHistoryView.as_view(), name='orders'),
    path('orders/<str:order_number>/', views.AccountOrderDetailView.as_view(), name='order_detail'),
    path('addresses/', views.AddressBookView.as_view(), name='addresses'),
    path('wishlist/', views.WishlistView.as_view(), name='wishlist'),
    path('api/wishlist/toggle/', views.ToggleWishlistAPI.as_view(), name='api_toggle_wishlist'),
]
