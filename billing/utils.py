import iyzipay
from django.conf import settings
import json

class IyzicoService:
    def __init__(self):
        self.mock_mode = getattr(settings, 'IYZICO_MOCK_MODE', False)
        if not self.mock_mode:
            self.options = iyzipay.Options()
            self.options.api_key = settings.IYZICO_API_KEY
            self.options.secret_key = settings.IYZICO_SECRET_KEY
            self.options.base_url = settings.IYZICO_BASE_URL
        else:
            self.options = None

    def initialize_checkout_form(self, user, plan, callback_url):
        if self.mock_mode:
            # Generate Mock Form content
            # This form POSTs to callbackUrl with a token
            mock_token = f"mock_{plan.id}"
            html_content = f"""
            <div class="alert alert-info">
                <h4>Test Modu Aktif</h4>
                <p>Gerçek Iyzico API kullanılmamaktadır. Test için aşağıdaki butona basın.</p>
                <form action="{callback_url}" method="post">
                    <input type="hidden" name="token" value="{mock_token}">
                    <button type="submit" class="btn btn-success btn-lg w-100">Ödemeyi Başarıyla Tamamla (Test)</button>
                </form>
            </div>
            """
            
            return json.dumps({
                'status': 'success',
                'checkoutFormContent': html_content,
                'token': mock_token
            })

        request = {
            'locale': 'tr',
            'conversationId': f'sub_{user.id}_{plan.id}',
            'price': str(plan.price_monthly),
            'paidPrice': str(plan.price_monthly),
            'currency': iyzipay.Currency.TRY,
            'basketId': f'B{plan.id}',
            'paymentGroup': iyzipay.PaymentGroup.PRODUCT,
            'callbackUrl': callback_url,
            'enabledInstallments': [1],
            'buyer': {
                'id': str(user.id),
                'name': getattr(user, 'first_name', 'Misafir') or 'Misafir',
                'surname': getattr(user, 'last_name', 'Kullanici') or 'Kullanici',
                'gsmNumber': '+905300000000',
                'email': user.email,
                'identityNumber': '11111111111',
                'lastLoginDate': '2015-10-05 12:43:35',
                'registrationDate': '2013-04-21 15:12:09',
                'registrationAddress': 'Istanbul',
                'ip': '85.34.78.112',
                'city': 'Istanbul',
                'country': 'Turkey',
                'zipCode': '34732'
            },
            'shippingAddress': {
                'contactName': 'Test User', 'city': 'Istanbul', 'country': 'Turkey', 'address': 'Test Adres', 'zipCode': '34742'
            },
            'billingAddress': {
                'contactName': 'Test User', 'city': 'Istanbul', 'country': 'Turkey', 'address': 'Test Adres', 'zipCode': '34742'
            },
            'basketItems': [
                {
                    'id': str(plan.id),
                    'name': plan.name,
                    'category1': 'SaaS',
                    'itemType': iyzipay.BasketItemType.VIRTUAL,
                    'price': str(plan.price_monthly)
                }
            ]
        }
        
        checkout_form_initialize = iyzipay.CheckoutFormInitialize().create(request, self.options)
        return checkout_form_initialize.read().decode('utf-8')

    def retrieve_checkout_form(self, token):
        if self.mock_mode and token.startswith('mock_'):
            # Parse plan id from token
            try:
                plan_id = token.split('_')[1]
                return json.dumps({
                    'paymentStatus': 'SUCCESS',
                    'basketId': f'B{plan_id}',
                    'status': 'success'
                })
            except:
                return json.dumps({'status': 'failure'})
                
        request = {
            'locale': 'tr',
            'token': token
        }
        checkout_form = iyzipay.CheckoutForm().retrieve(request, self.options)
        return checkout_form.read().decode('utf-8')
