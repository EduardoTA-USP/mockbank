from enum import unique
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Sum
from djmoney.models.fields import MoneyField
import datetime
from django.contrib import admin

from django.contrib.auth.models import AbstractUser

class Customer(AbstractUser):
    name = models.TextField()
    cpf = models.IntegerField(unique=True, null=True)
    phone_number = models.IntegerField(unique=True, null=True)

    class Meta:
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'
    
    def __str__(self):
        return f'{self.name}, {self.cpf}'

class BankAccount(models.Model):
    account_id = models.BigAutoField(primary_key=True)
    account_number = models.IntegerField()
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)

    balance_is_up_to_date = models.BooleanField(default=False)

    @admin.display(description='Balance')
    def get_balance(self):
        if not self.balance_is_up_to_date:
            balance_partie1 = Transaction.objects.filter(partie1=self).aggregate(Sum('transaction_amount'))['transaction_amount__sum']
            balance_partie2 = Transaction.objects.filter(partie2=self).aggregate(Sum('transaction_amount'))['transaction_amount__sum']

            return balance_partie1-balance_partie2

    def __str__(self):
        return f'{self.customer.name} - CPF: {self.customer.cpf}'

class Transaction(models.Model):
    transaction_id = models.BigAutoField(primary_key=True)
    transaction_amount = MoneyField(max_digits=14, decimal_places=2, default_currency='BRL')
    transaction_name = models.TextField()
    transaction_date = models.DateField(default=datetime.date.today)
    partie1 = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='partie1')
    partie2 = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='partie2')
