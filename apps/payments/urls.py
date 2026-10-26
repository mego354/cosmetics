from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('payments/paymob/callback/', views.PaymobCallbackView.as_view(), name='paymob_callback'),
    path('payments/paymob/webhook/', views.PaymobWebhookView.as_view(), name='paymob_webhook'),
    path('payments/paymob/<str:order_number>/', views.PaymobInitiateView.as_view(), name='paymob_initiate'),
]
