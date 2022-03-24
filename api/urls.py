from django.urls import path, include
from .views import account_balances

urlpatterns = [
    path('balances/', account_balances, name='account_balances'),
]