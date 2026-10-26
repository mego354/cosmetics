from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('api/checkout/validate-coupon/', views.ValidateCouponAPI.as_view(), name='api_validate_coupon'),
    path('order/<str:order_number>/', views.OrderConfirmationView.as_view(), name='confirmation'),
    path('track-order/', views.OrderTrackView.as_view(), name='track_order'),
    path('track-order/<str:tracking_number>/', views.OrderTrackView.as_view(), name='order_track'),
    path('track-order/<str:tracking_number>/', views.OrderTrackView.as_view(), name='track_order_detail'),
]
