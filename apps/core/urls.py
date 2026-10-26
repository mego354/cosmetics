from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('switch-lang/<str:lang_code>/', views.SwitchLanguageView.as_view(), name='switch_language'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('rituals/', views.RitualsView.as_view(), name='rituals'),
    path('stories/', views.StoriesView.as_view(), name='stories'),
]
