from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.accounts.models import User
from apps.orders.models import Order


class Payment(models.Model):
    STATUS_CHOICES = [
        ('initiated', _('تم البدء (Initiated)')),
        ('pending', _('قيد المعالجة البنكية (Pending)')),
        ('successful', _('نجحت العملية (Successful)')),
        ('failed', _('فشلت العملية (Failed)')),
        ('cancelled', _('تم الإلغاء من قبل المستخدم (Cancelled)')),
        ('refunded', _('مستردة (Refunded)')),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments', verbose_name=_('الطلب'))
    payment_method = models.CharField(_('طريقة الدفع'), max_length=50)
    amount = models.DecimalField(_('المبلغ المسدد (ج.م)'), max_digits=10, decimal_places=2)
    currency = models.CharField(_('العملة'), max_length=10, default='EGP')
    status = models.CharField(_('حالة الدفع'), max_length=30, choices=STATUS_CHOICES, default='initiated')
    
    transaction_id = models.CharField(_('رقم المعاملة الداخلي'), max_length=150, blank=True, db_index=True)
    paymob_order_id = models.CharField(_('رقم طلب Paymob'), max_length=150, blank=True, db_index=True)
    paymob_transaction_id = models.CharField(_('رقم معاملة Paymob البنكية'), max_length=150, blank=True, db_index=True)
    
    error_message = models.TextField(_('رسالة الخطأ إن وجدت'), blank=True)
    raw_response = models.JSONField(_('الرد الخام من بوابة الدفع'), default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('معاملة دفع')
        verbose_name_plural = _('معاملات الدفع')
        ordering = ['-created_at']

    def __str__(self):
        return f"دفع {self.amount} ج.م لطلب {self.order.order_number} ({self.get_status_display()})"


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications', verbose_name=_('المستخدم'))
    title_ar = models.CharField(_('عنوان الإشعار بالعربية'), max_length=200)
    title_en = models.CharField(_('عنوان الإشعار بالإنجليزية'), max_length=200, blank=True)
    message_ar = models.TextField(_('نص الإشعار بالعربية'))
    message_en = models.TextField(_('نص الإشعار بالإنجليزية'), blank=True)
    link = models.CharField(_('رابط الوجهة'), max_length=255, blank=True)
    is_read = models.BooleanField(_('تمت القراءة'), default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('إشعار')
        verbose_name_plural = _('الإشعارات')
        ordering = ['-created_at']

    def __str__(self):
        return self.title_ar
