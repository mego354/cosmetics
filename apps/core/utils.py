from django.conf import settings


def get_current_lang(request):
    """Retrieve current language code ('ar' or 'en'). Default is 'ar'."""
    lang = request.session.get('django_language') or request.COOKIES.get(
        getattr(settings, 'LANGUAGE_COOKIE_NAME', 'django_language'), 'ar'
    )
    return 'en' if lang == 'en' else 'ar'


def get_localized_str(request, ar_str, en_str):
    """Returns ar_str or en_str depending on user's active language."""
    return en_str if get_current_lang(request) == 'en' else ar_str
