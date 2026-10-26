import hashlib
import hmac
import logging
import requests
from decimal import Decimal
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class PaymobService:
    """
    Server-Side Paymob Egypt Integration Service
    Implements authentication, order registration, payment key generation,
    and HMAC verification for cards, Meeza, and mobile wallets.
    """

    def __init__(self):
        self.api_key = getattr(settings, 'PAYMOB_API_KEY', '')
        self.integration_id = getattr(settings, 'PAYMOB_INTEGRATION_ID', '')
        self.iframe_id = getattr(settings, 'PAYMOB_IFRAME_ID', '')
        self.hmac_secret = getattr(settings, 'PAYMOB_HMAC_SECRET', '')
        self.base_url = getattr(settings, 'PAYMOB_BASE_URL', 'https://accept.paymob.com/api')

    def get_auth_token(self):
        """Step 1: Authenticate and obtain auth token from Paymob"""
        url = f"{self.base_url}/auth/tokens"
        try:
            response = requests.post(url, json={"api_key": self.api_key}, timeout=15)
            if response.status_code == 201 or response.status_code == 200:
                data = response.json()
                return data.get('token')
            logger.error(f"Paymob auth failed: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"Paymob auth error: {e}")
        return None

    def register_paymob_order(self, auth_token, order):
        """Step 2: Register the order on Paymob to obtain paymob_order_id"""
        url = f"{self.base_url}/ecommerce/orders"
        amount_cents = int(order.total * Decimal('100'))
        payload = {
            "auth_token": auth_token,
            "delivery_needed": "false",
            "amount_cents": str(amount_cents),
            "currency": "EGP",
            "merchant_order_id": str(order.order_number),
            "items": [
                {
                    "name": item.product_name,
                    "amount_cents": str(int(item.unit_price * Decimal('100'))),
                    "description": item.variant_title or item.product_name,
                    "quantity": str(item.quantity)
                } for item in order.items.all()
            ]
        }
        try:
            response = requests.post(url, json=payload, timeout=15)
            if response.status_code in (200, 201):
                return response.json().get('id')
            logger.error(f"Paymob order registration failed: {response.text}")
        except Exception as e:
            logger.error(f"Paymob register order exception: {e}")
        return None

    def generate_payment_key(self, auth_token, paymob_order_id, order):
        """Step 3: Generate payment key token for the user to checkout"""
        url = f"{self.base_url}/acceptance/payment_keys"
        amount_cents = int(order.total * Decimal('100'))
        
        # Split customer name
        name_parts = (order.customer_name or 'Client Lume').strip().split()
        first_name = name_parts[0] if name_parts else 'Valued'
        last_name = name_parts[-1] if len(name_parts) > 1 else 'Client'

        payload = {
            "auth_token": auth_token,
            "amount_cents": str(amount_cents),
            "expiration": 3600,
            "order_id": str(paymob_order_id),
            "billing_data": {
                "apartment": "NA",
                "email": order.customer_email or "concierge@lume-beauty.eg",
                "floor": "NA",
                "first_name": first_name,
                "street": (order.shipping_address.street_address if order.shipping_address else "Cairo")[:50],
                "building": "NA",
                "phone_number": order.customer_phone or "+201000000000",
                "shipping_method": "PKG",
                "postal_code": "NA",
                "city": (order.shipping_address.city if order.shipping_address else "Cairo")[:50],
                "country": "EG",
                "last_name": last_name,
                "state": (order.shipping_address.get_governorate_display() if order.shipping_address else "Cairo")[:50]
            },
            "currency": "EGP",
            "integration_id": int(self.integration_id) if self.integration_id.isdigit() else 4589214,
            "lock_order_when_paid": "true"
        }
        try:
            response = requests.post(url, json=payload, timeout=15)
            if response.status_code in (200, 201):
                return response.json().get('token')
            logger.error(f"Paymob payment key generation failed: {response.text}")
        except Exception as e:
            logger.error(f"Paymob payment key exception: {e}")
        return None

    def get_iframe_url(self, payment_key_token):
        """Construct secure iframe URL for redirection"""
        return f"https://accept.paymob.com/api/acceptance/iframes/{self.iframe_id}?payment_token={payment_key_token}"

    def verify_hmac(self, data):
        """
        Calculates SHA512 HMAC according to Paymob's specifications:
        Concatenate in order:
        amount_cents, created_at, currency, error_occured, has_parent_transaction,
        id, integration_id, is_3d_secure, is_auth, is_capture, is_refunded,
        is_standalone_payment, is_voided, order.id, owner, pending,
        source_data.pan, source_data.sub_type, source_data.type, success
        """
        if not self.hmac_secret:
            return True  # Development mode fallback

        try:
            received_hmac = data.get('hmac', '')
            if not received_hmac:
                return False

            obj = data.get('obj', data)
            order_info = obj.get('order', {})
            source_data = obj.get('source_data', {})

            fields = [
                str(obj.get('amount_cents', '')),
                str(obj.get('created_at', '')),
                str(obj.get('currency', '')),
                str(obj.get('error_occured', '')).lower(),
                str(obj.get('has_parent_transaction', '')).lower(),
                str(obj.get('id', '')),
                str(obj.get('integration_id', '')),
                str(obj.get('is_3d_secure', '')).lower(),
                str(obj.get('is_auth', '')).lower(),
                str(obj.get('is_capture', '')).lower(),
                str(obj.get('is_refunded', '')).lower(),
                str(obj.get('is_standalone_payment', '')).lower(),
                str(obj.get('is_voided', '')).lower(),
                str(order_info.get('id', '')),
                str(obj.get('owner', '')),
                str(obj.get('pending', '')).lower(),
                str(source_data.get('pan', '')),
                str(source_data.get('sub_type', '')),
                str(source_data.get('type', '')),
                str(obj.get('success', '')).lower(),
            ]

            concatenated = "".join(fields)
            calculated_hmac = hmac.new(
                self.hmac_secret.encode('utf-8'),
                concatenated.encode('utf-8'),
                hashlib.sha512
            ).hexdigest()

            return hmac.compare_digest(calculated_hmac.lower(), received_hmac.lower())
        except Exception as e:
            logger.error(f"HMAC verification error: {e}")
            return False
