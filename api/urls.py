from django.urls import path, include
from .views import account_balances, transactions

urlpatterns = [
    path('balances/', account_balances, name='account_balances'),
    path('transactions/', transactions, name='transactions')
]