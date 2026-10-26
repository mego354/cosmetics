from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import View
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.db import transaction
import json
import logging
from .models import Payment, Notification
from .paymob import PaymobService
from apps.orders.models import Order

logger = logging.getLogger(__name__)


class PaymobInitiateView(View):
    def get(self, request, order_number):
        order = get_object_or_404(Order, order_number=order_number)
        
        # Don't re-initiate if already paid
        if order.payment_status == 'paid':
            return redirect('orders:confirmation', order_number=order.order_number)

        paymob = PaymobService()
        auth_token = paymob.get_auth_token()
        
        iframe_url = None
        payment_key = None

        if auth_token:
            paymob_order_id = paymob.register_paymob_order(auth_token, order)
            if paymob_order_id:
                payment_key = paymob.generate_payment_key(auth_token, paymob_order_id, order)
                if payment_key:
                    iframe_url = paymob.get_iframe_url(payment_key)
                    # Record initiated payment
                    Payment.objects.create(
                        order=order,
                        payment_method='paymob_card',
                        amount=order.total,
                        currency='EGP',
                        status='pending',
                        paymob_order_id=str(paymob_order_id),
                        transaction_id=str(payment_key)[:30],
                    )

        context = {
            'order': order,
            'iframe_url': iframe_url,
            'payment_key': payment_key,
        }
        return render(request, 'payments/paymob_checkout.html', context)


class PaymobCallbackView(View):
    def get(self, request):
        """Transaction Response Callback (Browser Redirect from Paymob)"""
        params = request.GET.dict()
        success = params.get('success', 'false').lower() == 'true'
        order_id = params.get('order')
        merchant_order_id = params.get('merchant_order_id')
        transaction_id = params.get('id')

        paymob = PaymobService()
        is_authentic = paymob.verify_hmac(params)

        order = None
        if merchant_order_id:
            order = Order.objects.filter(order_number=merchant_order_id).first()
        elif order_id:
            payment = Payment.objects.filter(paymob_order_id=order_id).first()
            if payment:
                order = payment.order

        from apps.core.utils import get_localized_str
        if not order:
            messages.error(
                request, 
                get_localized_str(request, 'تعذر التحقق من مرجع الطلب المحدد.', 'Could not verify the specified order reference.')
            )
            return redirect('core:home')

        with transaction.atomic():
            payment, _ = Payment.objects.get_or_create(
                order=order,
                defaults={
                    'payment_method': 'paymob_card',
                    'amount': order.total,
                    'currency': 'EGP',
                }
            )
            payment.paymob_transaction_id = transaction_id or ''
            payment.raw_response = params

            if success and is_authentic:
                payment.status = 'successful'
                payment.save()
                
                order.payment_status = 'paid'
                order.status = 'processing'
                order.save(update_fields=['payment_status', 'status'])

                if order.user:
                    Notification.objects.create(
                        user=order.user,
                        title_ar='تم سداد طلبكِ بنجاح',
                        message_ar=f'تم تأكيد عملية الدفع البنكية للطلب #{order.order_number} بنجاح.',
                        link=f'/order/{order.order_number}/'
                    )

                messages.success(
                    request, 
                    get_localized_str(request, 'تمت عملية الدفع الإلكتروني بنجاح تام!', 'Online card payment completed successfully!')
                )
                return redirect('orders:confirmation', order_number=order.order_number)
            else:
                payment.status = 'failed'
                payment.error_message = params.get('data.message', 'فشلت عملية الدفع الإلكتروني')
                payment.save()
                
                order.payment_status = 'failed'
                order.save(update_fields=['payment_status'])
                
                messages.error(
                    request, 
                    get_localized_str(
                        request, 
                        'تعذر إتمام الدفع بالبطاقة البنكية. يمكنكِ إعادة المحاولة أو اختيار الدفع عند الاستلام.', 
                        'Card payment could not be completed. You can re-try or switch to Cash on Delivery.'
                    )
                )
                return render(request, 'payments/payment_failed.html', {'order': order})


@method_decorator(csrf_exempt, name='dispatch')
class PaymobWebhookView(View):
    def post(self, request):
        """Server-to-Server Webhook Transaction Callback"""
        try:
            payload = json.loads(request.body)
            paymob = PaymobService()
            
            if not paymob.verify_hmac(payload):
                logger.warning("Paymob webhook HMAC verification failed!")
                return HttpResponse(status=400)

            obj = payload.get('obj', {})
            success = obj.get('success', False)
            order_info = obj.get('order', {})
            merchant_order_id = order_info.get('merchant_order_id')
            transaction_id = str(obj.get('id', ''))

            if merchant_order_id:
                order = Order.objects.filter(order_number=merchant_order_id).first()
                if order:
                    payment, _ = Payment.objects.get_or_create(
                        order=order,
                        defaults={'payment_method': 'paymob_card', 'amount': order.total, 'currency': 'EGP'}
                    )
                    payment.paymob_transaction_id = transaction_id
                    payment.raw_response = payload
                    
                    if success:
                        payment.status = 'successful'
                        order.payment_status = 'paid'
                        order.status = 'processing'
                    else:
                        payment.status = 'failed'
                        order.payment_status = 'failed'
                        
                    payment.save()
                    order.save(update_fields=['payment_status', 'status'])

            return HttpResponse(status=200)
        except Exception as e:
            logger.error(f"Paymob webhook processing exception: {e}")
            return HttpResponse(status=500)
