from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls', namespace='core')),
    path('', include('apps.catalog.urls', namespace='catalog')),
    path('', include('apps.cart.urls', namespace='cart')),
    path('', include('apps.orders.urls', namespace='orders')),
    path('', include('apps.payments.urls', namespace='payments')),
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
