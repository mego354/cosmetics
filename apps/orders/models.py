from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
import uuid
from apps.accounts.models import User, Address
from apps.catalog.models import Product, ProductVariant


class Coupon(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', _('نسبة مئوية (%)')),
        ('fixed', _('مبلغ ثابت (ج.م)')),
    ]

    code = models.CharField(_('رمز القسيمة'), max_length=50, unique=True)
    description = models.CharField(_('وصف القسيمة الترويجية'), max_length=255, blank=True)
    discount_type = models.CharField(_('نوع الخصم'), max_length=20, choices=DISCOUNT_TYPE_CHOICES, default='percentage')
    discount_value = models.DecimalField(_('قيمة الخصم'), max_digits=10, decimal_places=2)
    min_order_value = models.DecimalField(_('الحد الأدنى للطلب (ج.م)'), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    max_discount_amount = models.DecimalField(_('الحد الأقصى لمبلغ الخصم (ج.م)'), max_digits=10, decimal_places=2, null=True, blank=True)
    max_uses = models.PositiveIntegerField(_('أقصى عدد للاستخدام'), null=True, blank=True)
    used_count = models.PositiveIntegerField(_('مرات الاستخدام الفعلية'), default=0)
    is_active = models.BooleanField(_('نشط ومتاح للتطبيق'), default=True)
    valid_from = models.DateTimeField(_('صالح من تاريخ'), default=timezone.now)
    valid_to = models.DateTimeField(_('صالح حتى تاريخ'), null=True, blank=True)

    class Meta:
        verbose_name = _('قسيمة ترويجية / كود خصم')
        verbose_name_plural = _('قسائم الترويج وأكواد الخصم')

    def __str__(self):
        return f"{self.code} ({self.discount_value}{'%' if self.discount_type == 'percentage' else ' ج.م'})"

    def is_valid_now(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_to and now > self.valid_to:
            return False
        if self.max_uses and self.used_count >= self.max_uses:
            return False
        return True

    def calculate_discount(self, subtotal):
        if not self.is_valid_now() or subtotal < self.min_order_value:
            return Decimal('0.00')

        if self.discount_type == 'percentage':
            discount = (subtotal * self.discount_value) / Decimal('100.00')
        else:
            discount = min(self.discount_value, subtotal)

        if self.max_discount_amount and discount > self.max_discount_amount:
            discount = self.max_discount_amount

        return round(discount, 2)


class ShippingMethod(models.Model):
    name_ar = models.CharField(_('اسم طريقة الشحن بالعربية'), max_length=150)
    name_en = models.CharField(_('اسم طريقة الشحن بالإنجليزية'), max_length=150)
    code = models.CharField(_('كود التعريف'), max_length=50, unique=True)
    delivery_time_ar = models.CharField(_('مدة التوصيل بالعربية'), max_length=100, default='خلال 24-48 ساعة')
    delivery_time_en = models.CharField(_('مدة التوصيل بالإنجليزية'), max_length=100, default='Within 24-48 hours')
    cost = models.DecimalField(_('تكلفة الشحن (ج.م)'), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    free_threshold = models.DecimalField(_('حد الشحن المجاني (ج.م)'), max_digits=10, decimal_places=2, default=Decimal('800.00'))
    is_active = models.BooleanField(_('نشط'), default=True)

    class Meta:
        verbose_name = _('طريقة الشحن والتوصيل')
        verbose_name_plural = _('طرق الشحن والتوصيل')

    def __str__(self):
        return f"{self.name_ar} ({self.cost} ج.م)"

    def get_effective_cost(self, subtotal):
        if self.free_threshold and subtotal >= self.free_threshold:
            return Decimal('0.00')
        return self.cost


class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('pending', _('قيد المراجعة (Pending)')),
        ('payment_pending', _('بانتظار تأكيد الدفع (Payment Pending)')),
        ('paid', _('تم سداد القيمة (Paid)')),
        ('processing', _('جاري المعالجة (Processing)')),
        ('preparing', _('جاري التجهيز والتغليف الملكي (Preparing)')),
        ('shipped', _('تم تسليم الشحنة للمندوب (Shipped)')),
        ('out_for_delivery', _('خرج للتوصيل اليوم (Out for Delivery)')),
        ('delivered', _('تم التوصيل بنجاح (Delivered)')),
        ('cancelled', _('ملغي (Cancelled)')),
        ('returned', _('مرتجع (Returned)')),
        ('refunded', _('مسترد (Refunded)')),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('cod', _('الدفع نقدياً عند الاستلام مع حق المعاينة (Cash on Delivery)')),
        ('paymob_card', _('بطاقات فيزا / ماستركارد وميزة الوطنية (Paymob)')),
        ('instapay_wallet', _('إنستاباي ومحافظ المحمول (Vodafone Cash / InstaPay)')),
        ('valu_installments', _('تقسيط ميسر عبر ValU أو تاباي (Installments)')),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', _('معلق (Pending)')),
        ('authorized', _('مفوض (Authorized)')),
        ('paid', _('مدفوع بنجاح (Paid)')),
        ('failed', _('فشلت المحاولة (Failed)')),
        ('refunded', _('مسترد (Refunded)')),
        ('cancelled', _('ملغي (Cancelled)')),
    ]

    order_number = models.CharField(_('رقم الطلب المرجعي'), max_length=50, unique=True, db_index=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders', verbose_name=_('المستخدم'))
    session_key = models.CharField(_('معرف الجلسة للزائر'), max_length=100, blank=True)
    
    # Customer Details
    customer_name = models.CharField(_('اسم العميل بالكامل'), max_length=150)
    customer_email = models.EmailField(_('البريد الإلكتروني'), blank=True)
    customer_phone = models.CharField(_('رقم الهاتف للتواصل'), max_length=25)
    
    # Address Link & Immutable Snapshot
    shipping_address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    shipping_address_snapshot = models.JSONField(_('بيانات العنوان المحفوظة للطلب'), default=dict)
    
    # Logistics & Promo
    shipping_method = models.ForeignKey(ShippingMethod, on_delete=models.SET_NULL, null=True, blank=True)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Lifecycle States
    status = models.CharField(_('حالة الطلب'), max_length=30, choices=ORDER_STATUS_CHOICES, default='pending')
    payment_method = models.CharField(_('طريقة الدفع'), max_length=50, choices=PAYMENT_METHOD_CHOICES, default='cod')
    payment_status = models.CharField(_('حالة الدفع'), max_length=30, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # Monetary Values in EGP
    subtotal = models.DecimalField(_('مجموع المنتجات (ج.م)'), max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(_('مبلغ الخصم (ج.م)'), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    shipping_cost = models.DecimalField(_('تكلفة الشحن (ج.م)'), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    vat_amount = models.DecimalField(_('ضريبة القيمة المضافة 14% (مشمولة)'), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total = models.DecimalField(_('الإجمالي النهائي المطلوب (ج.م)'), max_digits=10, decimal_places=2)
    currency = models.CharField(_('العملة'), max_length=10, default='EGP')
    
    # Experience Enhancers
    whatsapp_opt_in = models.BooleanField(_('تأكيد الموعد وإرسال التتبع عبر WhatsApp'), default=True)
    customer_notes = models.TextField(_('ملاحظات خاصة بالعميل'), blank=True)
    admin_notes = models.TextField(_('ملاحظات الإدارة الداخلية'), blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('طلب شراء')
        verbose_name_plural = _('طلبات الشراء')
        ordering = ['-created_at']

    def __str__(self):
        return f"طلب {self.order_number} - {self.customer_name} ({self.total} ج.م)"

    @property
    def grand_total(self):
        return self.total

    @classmethod
    def generate_order_number(cls):
        random_suffix = uuid.uuid4().hex[:6].upper()
        year = timezone.now().strftime('%Y')
        return f"LME-{year}-{random_suffix}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name=_('الطلب'))
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name='order_items')
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(_('اسم المستحضر وقت الطلب'), max_length=255)
    variant_title = models.CharField(_('اسم الخيار (حجم/درجة)'), max_length=100, blank=True)
    sku = models.CharField(_('رمز SKU'), max_length=100)
    unit_price = models.DecimalField(_('سعر الوحدة وقت الشراء (ج.م)'), max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(_('الكمية'), default=1)
    line_total = models.DecimalField(_('إجمالي البند (ج.م)'), max_digits=10, decimal_places=2)
    product_image_url = models.CharField(_('رابط صورة المستحضر'), max_length=500, blank=True)

    class Meta:
        verbose_name = _('عنصر بطلب الشراء')
        verbose_name_plural = _('عناصر طلبات الشراء')

    def __str__(self):
        return f"{self.quantity}x {self.product_name} في {self.order.order_number}"


class Shipment(models.Model):
    STATUS_CHOICES = [
        ('preparing', _('قيد التغليف والإعداد بالمعمل')),
        ('dispatched', _('تم التسليم لشركة الشحن السريع')),
        ('in_transit', _('في الطريق بين المحافظات')),
        ('out_for_delivery', _('مع مندوب التوصيل للتسليم اليوم')),
        ('delivered', _('تم التسليم للعميلة بنجاح')),
        ('failed_attempt', _('تعذر التسليم / إعادة محاولة غداً')),
        ('returned', _('مرتجع للمستودع الرئيسي')),
    ]

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='shipment', verbose_name=_('الطلب'))
    tracking_number = models.CharField(_('رقم بوليصة التتبع'), max_length=100, unique=True, db_index=True)
    carrier_name = models.CharField(_('شركة التوصيل الفاخر'), max_length=100, default='LUMÉ Prestige Express')
    estimated_delivery_date = models.DateField(_('تاريخ التوصيل المتوقع'), null=True, blank=True)
    current_status = models.CharField(_('الحالة الحالية للشحنة'), max_length=50, choices=STATUS_CHOICES, default='preparing')
    status_history = models.JSONField(_('سجل مراحل وتاريخ الشحنة'), default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('شحنة وبوليصة توصيل')
        verbose_name_plural = _('شحنات وبوالص التوصيل')

    def __str__(self):
        return f"بوليصة #{self.tracking_number} لطلب {self.order.order_number}"

    def add_history_entry(self, status, note=''):
        history = list(self.status_history or [])
        history.append({
            'status': status,
            'note': note,
            'timestamp': timezone.now().isoformat(),
        })
        self.status_history = history
        self.current_status = status
        self.save()
