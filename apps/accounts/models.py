from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    phone_number = models.CharField(_('رقم الهاتف'), max_length=20, blank=True, db_index=True)
    is_verified = models.BooleanField(_('تم التحقق'), default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('مستخدم')
        verbose_name_plural = _('المستخدمون')

    def __str__(self):
        return self.get_full_name() or self.username


class CustomerProfile(models.Model):
    SKIN_TYPE_CHOICES = [
        ('dry', _('بشرة جافة')),
        ('oily', _('بشرة دهنية')),
        ('combination', _('بشرة مختلطة')),
        ('sensitive', _('بشرة حساسة')),
        ('normal', _('بشرة عادية')),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name=_('المستخدم'))
    avatar = models.ImageField(_('الصورة الشخصية'), upload_to='avatars/', null=True, blank=True)
    skin_type = models.CharField(_('نوع البشرة'), max_length=20, choices=SKIN_TYPE_CHOICES, blank=True)
    skin_concerns = models.TextField(_('اهتمامات البشرة'), blank=True)
    loyalty_points = models.PositiveIntegerField(_('نقاط الولاء'), default=100)
    newsletter_subscribed = models.BooleanField(_('اشتراك النشرة التحريرية'), default=True)

    class Meta:
        verbose_name = _('ملف العميل')
        verbose_name_plural = _('ملفات العملاء')

    def __str__(self):
        return f"ملف {self.user.username}"


class Address(models.Model):
    GOVERNORATE_CHOICES = [
        ('cairo', 'القاهرة (Cairo)'),
        ('giza', 'الجيزة (Giza)'),
        ('alexandria', 'الإسكندرية (Alexandria)'),
        ('qalyubia', 'القليوبية (Qalyubia)'),
        ('sharqia', 'الشرقية (Sharqia)'),
        ('dakahlia', 'الدقهلية (Dakahlia)'),
        ('gharbia', 'الغربية (Gharbia)'),
        ('monufia', 'المنوفية (Monufia)'),
        ('beheira', 'البحيرة (Beheira)'),
        ('kafr_el_sheikh', 'كفر الشيخ (Kafr El Sheikh)'),
        ('damietta', 'دمياط (Damietta)'),
        ('port_said', 'بورسعيد (Port Said)'),
        ('ismailia', 'الإسماعيلية (Ismailia)'),
        ('suez', 'السويس (Suez)'),
        ('red_sea', 'البحر الأحمر والغردقة (Red Sea)'),
        ('matrouh', 'مطروح والساحل الشمالي (Matrouh)'),
        ('north_sinai', 'شمال سيناء (North Sinai)'),
        ('south_sinai', 'جنوب سيناء وشرم الشيخ (South Sinai)'),
        ('faiyum', 'الفيوم (Faiyum)'),
        ('beni_suef', 'بني سويف (Beni Suef)'),
        ('minya', 'المنيا (Minya)'),
        ('asyut', 'أسيوط (Asyut)'),
        ('sohag', 'سوهاج (Sohag)'),
        ('qena', 'قنا (Qena)'),
        ('luxor', 'الأقصر (Luxor)'),
        ('aswan', 'أسوان (Aswan)'),
        ('new_valley', 'الوادي الجديد (New Valley)'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='addresses', verbose_name=_('المستخدم'))
    session_key = models.CharField(_('معرف الجلسة للزائر'), max_length=100, blank=True, db_index=True)
    full_name = models.CharField(_('الاسم بالكامل'), max_length=150)
    phone_number = models.CharField(_('رقم الهاتف'), max_length=20)
    alternate_phone = models.CharField(_('رقم هاتف إضافي'), max_length=20, blank=True)
    governorate = models.CharField(_('المحافظة'), max_length=50, choices=GOVERNORATE_CHOICES, default='cairo')
    city = models.CharField(_('المدينة / الحي'), max_length=100, help_text=_('مثال: الزمالك / مصر الجديدة / التجمع'))
    street_address = models.CharField(_('اسم الشارع ورقم العمارة'), max_length=255)
    building_number = models.CharField(_('رقم المبنى'), max_length=50, blank=True)
    floor_number = models.CharField(_('رقم الطابق'), max_length=50, blank=True)
    apartment_number = models.CharField(_('رقم الشقة'), max_length=50, blank=True)
    nearest_landmark = models.CharField(_('علامة مميزة قريبة'), max_length=255, blank=True)
    delivery_instructions = models.TextField(_('ملاحظات خاصة بالتوصيل'), blank=True)
    is_default = models.BooleanField(_('العنوان الافتراضي'), default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('عنوان التوصيل')
        verbose_name_plural = _('عناوين التوصيل')
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f"{self.full_name} - {self.get_governorate_display()}, {self.city}"

    def save(self, *args, **kwargs):
        if self.is_default and self.user:
            Address.objects.filter(user=self.user, is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)
