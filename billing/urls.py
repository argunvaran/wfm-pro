from django.urls import path
from .views import pricing_page, init_payment, payment_callback

urlpatterns = [
    path('pricing/', pricing_page, name='pricing'),
    path('pay/<int:plan_id>/', init_payment, name='init_payment'),
    path('callback/', payment_callback, name='payment_callback'),
]
