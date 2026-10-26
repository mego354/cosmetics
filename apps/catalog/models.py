from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from apps.accounts.models import User


class Category(models.Model):
    name_ar = models.CharField(_('اسم الفئة بالعربية'), max_length=150)
    name_en = models.CharField(_('اسم الفئة بالإنجليزية'), max_length=150)
    slug = models.SlugField(max_length=150, unique=True)
    volume_number = models.CharField(_('رقم المجلد التحريري'), max_length=20, default='VOL. I', blank=True)
    french_subtitle = models.CharField(_('العنوان الفرعي بالفرنسية'), max_length=100, blank=True)
    description_ar = models.TextField(_('الوصف بالعربية'), blank=True)
    description_en = models.TextField(_('الوصف بالإنجليزية'), blank=True)
    image = models.CharField(_('رابط صورة الفئة'), max_length=500, blank=True)
    is_featured = models.BooleanField(_('فئة مميزة في الصفحة الرئيسية'), default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = _('فئة المنتجات')
        verbose_name_plural = _('فئات المنتجات')
        ordering = ['sort_order', 'id']

    def __str__(self):
        return f"{self.volume_number} • {self.name_ar} ({self.name_en})"


class Subcategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories', verbose_name=_('الفئة الرئيسية'))
    name_ar = models.CharField(_('اسم الفئة الفرعية بالعربية'), max_length=150)
    name_en = models.CharField(_('اسم الفئة الفرعية بالإنجليزية'), max_length=150)
    slug = models.SlugField(max_length=150, unique=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = _('فئة فرعية')
        verbose_name_plural = _('فئات فرعية')
        ordering = ['sort_order', 'id']

    def __str__(self):
        return f"{self.category.name_ar} -> {self.name_ar}"


class Brand(models.Model):
    name_ar = models.CharField(_('اسم العلامة بالعربية'), max_length=150)
    name_en = models.CharField(_('اسم العلامة بالإنجليزية'), max_length=150)
    slug = models.SlugField(max_length=150, unique=True)
    description_ar = models.TextField(_('الوصف بالعربية'), blank=True)
    description_en = models.TextField(_('الوصف بالإنجليزية'), blank=True)
    logo = models.CharField(_('رابط الشعار'), max_length=500, blank=True)

    class Meta:
        verbose_name = _('العلامة التجارية')
        verbose_name_plural = _('العلامات التجارية')

    def __str__(self):
        return self.name_ar


class Product(models.Model):
    RITUAL_CHOICES = [
        ('all', _('جميع الطقوس والاحتياجات')),
        ('radiance', _('النضارة والإشراق الملكي')),
        ('hydration', _('الترطيب ومكافحة الجفاف')),
        ('soothing', _('تهدئة البشرة الحساسة')),
        ('anti-aging', _('الشد ومكافحة التجاعيد')),
    ]

    SKIN_TYPE_CHOICES = [
        ('all', _('جميع أنواع البشرة')),
        ('dry', _('البشرة الجافة')),
        ('sensitive', _('البشرة الحساسة')),
        ('oily', _('البشرة الدهنية والمعرضة للشوائب')),
        ('combination', _('البشرة المختلطة')),
        ('normal', _('البشرة العادية')),
    ]

    name_ar = models.CharField(_('اسم المستحضر بالعربية'), max_length=255)
    name_en = models.CharField(_('اسم المستحضر بالإنجليزية'), max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', verbose_name=_('الفئة'))
    subcategory = models.ForeignKey(Subcategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    sku = models.CharField(_('رمز المنتج SKU'), max_length=100, unique=True)
    
    # Pricing in EGP
    price = models.DecimalField(_('السعر الحالي (ج.م)'), max_digits=10, decimal_places=2)
    compare_at_price = models.DecimalField(_('السعر قبل الخصم (ج.م)'), max_digits=10, decimal_places=2, null=True, blank=True)
    cost_price = models.DecimalField(_('سعر التكلفة (ج.م)'), max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Stock
    stock = models.PositiveIntegerField(_('الكمية المتاحة في المخزن'), default=15)
    low_stock_threshold = models.PositiveIntegerField(_('حد التنبيه بنقص المخزون'), default=3)
    
    # Editorial Storytelling & Details
    short_description_ar = models.TextField(_('وصف مختصر بالعربية'), blank=True)
    short_description_en = models.TextField(_('وصف مختصر بالإنجليزية'), blank=True)
    description_ar = models.TextField(_('الوصف التحريري الكامل بالعربية'), blank=True)
    description_en = models.TextField(_('الوصف التحريري الكامل بالإنجليزية'), blank=True)
    editorial_quote_ar = models.TextField(_('اقتباس تحريري مميز بالعربية'), blank=True)
    editorial_quote_en = models.TextField(_('اقتباس تحريري مميز بالإنجليزية'), blank=True)
    formula_details_ar = models.TextField(_('تفاصيل التركيبة والأسرار المعملية'), blank=True)
    formula_details_en = models.TextField(_('تفاصيل التركيبة بالإنجليزية'), blank=True)
    usage_instructions_ar = models.TextField(_('طريقة الاستخدام والطقس اليومي'), blank=True)
    usage_instructions_en = models.TextField(_('طريقة الاستخدام بالإنجليزية'), blank=True)
    ingredients_ar = models.TextField(_('قائمة المكونات النباتية والفعالة'), blank=True)
    ingredients_en = models.TextField(_('قائمة المكونات بالإنجليزية'), blank=True)
    
    # Egyptian Provenance & Regulatory Trust Signals
    provenance_origin_ar = models.CharField(_('مصدر المكونات الطبيعية'), max_length=200, blank=True)
    provenance_origin_en = models.CharField(_('مصدر المكونات بالإنجليزية'), max_length=200, blank=True)
    ministry_registration_code = models.CharField(_('كود الترخيص بهيئة الدواء'), max_length=100, default='EG-EDA-2024-88', blank=True)
    
    # Flags & Filters
    ritual_type = models.CharField(_('الطقس / الحاجة الجمالية'), max_length=50, choices=RITUAL_CHOICES, default='all')
    target_skin_type = models.CharField(_('نوع البشرة المستهدف'), max_length=50, choices=SKIN_TYPE_CHOICES, default='all')
    express_shipping_eligible = models.BooleanField(_('مؤهل للشحن خلال 24 ساعة بمصر'), default=True)
    is_active = models.BooleanField(_('نشط ومتاح للطلب'), default=True)
    is_bestseller = models.BooleanField(_('الأكثر طلباً Best Seller'), default=False)
    is_featured = models.BooleanField(_('مختار في المعرض التحريري'), default=False)
    is_new_arrival = models.BooleanField(_('إصدار جديد New'), default=False)
    
    # Metrics
    average_rating = models.DecimalField(_('متوسط التقييم'), max_digits=3, decimal_places=2, default=Decimal('5.00'))
    reviews_count = models.PositiveIntegerField(_('عدد التقييمات الموثقة'), default=0)
    
    # SEO
    meta_title = models.CharField(_('عنوان السيو'), max_length=255, blank=True)
    meta_description = models.TextField(_('وصف السيو'), blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('مستحضر تجميل')
        verbose_name_plural = _('مستحضرات التجميل')
        ordering = ['-is_featured', '-is_bestseller', '-created_at']

    def __str__(self):
        return f"{self.name_ar} ({self.sku})"

    @property
    def is_in_stock(self):
        return self.stock > 0

    @property
    def has_discount(self):
        return self.compare_at_price and self.compare_at_price > self.price

    @property
    def discount_amount(self):
        if self.has_discount:
            return self.compare_at_price - self.price
        return Decimal('0.00')

    @property
    def discount_percentage(self):
        if self.has_discount and self.compare_at_price > 0:
            pct = ((self.compare_at_price - self.price) / self.compare_at_price) * 100
            return int(round(pct))
        return 0

    @property
    def primary_image(self):
        primary = self.images.filter(is_primary=True).first()
        if primary:
            return primary
        return self.images.first()

    @property
    def installment_amount(self):
        """Monthly installment for 4 months (ValU / Tabby style)"""
        return round(self.price / Decimal('4'), 2)


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', verbose_name=_('المستحضر'))
    image = models.CharField(_('رابط الصورة'), max_length=600)
    alt_text_ar = models.CharField(_('النص البديل بالعربية'), max_length=255, blank=True)
    alt_text_en = models.CharField(_('النص البديل بالإنجليزية'), max_length=255, blank=True)
    is_primary = models.BooleanField(_('الصورة الرئيسية'), default=False)
    plate_indicator = models.CharField(_('رقم اللوحة التحريرية'), max_length=50, blank=True, help_text='PLATE 01 — THE FORMULATION')
    plate_tag = models.CharField(_('وسم اللوحة المختصر'), max_length=20, blank=True, help_text='PL.01')
    plate_caption = models.CharField(_('شرح اللوحة التحريرية'), max_length=255, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = _('صورة المستحضر')
        verbose_name_plural = _('صور المستحضرات')
        ordering = ['sort_order', 'id']

    def __str__(self):
        return f"صورة {self.plate_tag or self.id} لـ {self.product.name_ar}"


class ProductVariant(models.Model):
    VARIANT_TYPE_CHOICES = [
        ('size', _('الحجم والسعة (مل)')),
        ('shade', _('الدرجة اللونية المخملية')),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants', verbose_name=_('المستحضر'))
    variant_type = models.CharField(_('نوع الخيار'), max_length=20, choices=VARIANT_TYPE_CHOICES, default='size')
    title_ar = models.CharField(_('اسم الخيار بالعربية'), max_length=100, help_text='مثال: 50 مل، درجة الورد البلدي 01')
    title_en = models.CharField(_('اسم الخيار بالإنجليزية'), max_length=100, help_text='Example: 50ml, Damask Rose 01')
    sku = models.CharField(_('رمز SKU للخيار'), max_length=100, unique=True)
    volume_ml = models.PositiveIntegerField(_('الحجم بالمليلتر'), null=True, blank=True)
    shade_color_hex = models.CharField(_('كود لون الدرجة HEX'), max_length=20, blank=True, help_text='#C86D51')
    badge_text_ar = models.CharField(_('شارة الخيار بالعربية'), max_length=100, blank=True, help_text='مثال: الأكثر طلباً، الأكثر توفيراً')
    badge_text_en = models.CharField(_('شارة الخيار بالإنجليزية'), max_length=100, blank=True)
    price = models.DecimalField(_('سعر هذا الخيار (ج.م)'), max_digits=10, decimal_places=2)
    compare_at_price = models.DecimalField(_('السعر قبل الخصم (ج.م)'), max_digits=10, decimal_places=2, null=True, blank=True)
    stock = models.PositiveIntegerField(_('المخزون المتاح لهذا الخيار'), default=10)
    is_default = models.BooleanField(_('الخيار الافتراضي المختار'), default=False)

    class Meta:
        verbose_name = _('خيار المستحضر (حجم/درجة)')
        verbose_name_plural = _('خيارات المستحضرات')
        ordering = ['price', 'id']

    def __str__(self):
        return f"{self.product.name_ar} - {self.title_ar} ({self.price} ج.م)"

    @property
    def has_discount(self):
        return self.compare_at_price and self.compare_at_price > self.price

    @property
    def discount_amount(self):
        if self.has_discount:
            return self.compare_at_price - self.price
        return Decimal('0.00')


class ProductReview(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews', verbose_name=_('المستحضر'))
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews')
    author_name = models.CharField(_('اسم صاحبة التقييم'), max_length=150)
    governorate = models.CharField(_('المحافظة'), max_length=100, default='القاهرة', blank=True)
    rating = models.PositiveSmallIntegerField(_('التقييم من 5'), default=5, choices=[(i, str(i)) for i in range(1, 6)])
    title = models.CharField(_('عنوان الرأي'), max_length=200, blank=True)
    comment = models.TextField(_('تفاصيل التجربة'))
    is_verified_purchase = models.BooleanField(_('شراء موثق ومعتمد'), default=True)
    is_approved = models.BooleanField(_('معتمد للنشر'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('تقييم ورأي العميل')
        verbose_name_plural = _('تقييمات وآراء العملاء')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.author_name} - {self.product.name_ar} ({self.rating} نجوم)"


class Wishlist(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='wishlist')
    session_key = models.CharField(_('معرف الجلسة'), max_length=100, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('قائمة المفضلة')
        verbose_name_plural = _('قوائم المفضلة')

    def __str__(self):
        return f"مفضلة {self.user.username if self.user else self.session_key}"


class WishlistItem(models.Model):
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlist_items')
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('عنصر بالمفضلة')
        verbose_name_plural = _('عناصر بالمفضلة')
        unique_together = ('wishlist', 'product', 'variant')

    def __str__(self):
        return f"{self.product.name_ar} في المفضلة"
