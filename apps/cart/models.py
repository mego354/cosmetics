from django.db import models
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from apps.accounts.models import User
from apps.catalog.models import Product, ProductVariant


class Cart(models.Model):
    FREE_SHIPPING_THRESHOLD = Decimal('800.00') # EGP for free express delivery
    GIFT_TIER_THRESHOLD = Decimal('1200.00') # EGP for free 15ml shea scrub

    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='cart', verbose_name=_('المستخدم'))
    session_key = models.CharField(_('معرف الجلسة'), max_length=100, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('حقيبة التسوق')
        verbose_name_plural = _('حقائب التسوق')

    def __str__(self):
        return f"حقيبة {self.user.username if self.user else self.session_key}"

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def subtotal(self):
        return sum(item.line_total for item in self.items.all())

    @property
    def qualifies_for_free_shipping(self):
        return self.subtotal >= self.FREE_SHIPPING_THRESHOLD

    @property
    def remaining_for_free_shipping(self):
        if self.qualifies_for_free_shipping:
            return Decimal('0.00')
        return max(Decimal('0.00'), self.FREE_SHIPPING_THRESHOLD - self.subtotal)

    @property
    def free_shipping_progress_pct(self):
        if self.FREE_SHIPPING_THRESHOLD <= 0:
            return 100
        pct = (self.subtotal / self.FREE_SHIPPING_THRESHOLD) * 100
        return min(100, int(round(pct)))

    @property
    def qualifies_for_complimentary_gift(self):
        return self.subtotal >= self.GIFT_TIER_THRESHOLD

    @property
    def remaining_for_complimentary_gift(self):
        if self.qualifies_for_complimentary_gift:
            return Decimal('0.00')
        return max(Decimal('0.00'), self.GIFT_TIER_THRESHOLD - self.subtotal)

    @property
    def gift_progress_pct(self):
        if self.GIFT_TIER_THRESHOLD <= 0:
            return 100
        pct = (self.subtotal / self.GIFT_TIER_THRESHOLD) * 100
        return min(100, int(round(pct)))


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items', verbose_name=_('الحقيبة'))
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_items', verbose_name=_('المستحضر'))
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True, related_name='cart_items', verbose_name=_('الخيار'))
    quantity = models.PositiveIntegerField(_('الكمية'), default=1)
    price_at_addition = models.DecimalField(_('السعر وقت الإضافة (ج.م)'), max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('عنصر بالحقيبة')
        verbose_name_plural = _('عناصر بالحقيبة')
        unique_together = ('cart', 'product', 'variant')

    def __str__(self):
        return f"{self.quantity}x {self.product.name_ar} ({self.variant.title_ar if self.variant else ''})"

    @property
    def unit_price(self):
        if self.variant:
            return self.variant.price
        return self.product.price

    @property
    def line_total(self):
        return self.unit_price * self.quantity

    @property
    def image_url(self):
        img = self.product.primary_image
        return img.image if img else ''
