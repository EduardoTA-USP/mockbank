from enum import unique
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Sum
from djmoney.models.fields import MoneyField
import datetime
from django.contrib import admin

from django.contrib.auth.models import AbstractUser

from django.utils import timezone
from django.db.models import Q

class Customer(AbstractUser):
    customer_id = models.TextField(editable=False, null=True)
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
    branch_number = models.IntegerField()
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, unique=True)

    # Como é só um MVP, usa-se floats para saldos
    # mas o certo é usar um integer cuja visualização é com vírgula
    def checking_sub_account_balance(self):
        transactions = Transaction.objects.filter(first_partie_bank_account=self).filter(Q(transaction_date__lte=timezone.now()))
        balance = 0.0
        for transaction in transactions:
            if transaction.first_partie_type_of_sub_account == 'CHECKING':
                if transaction.creditDebitType == 'CREDIT':
                    balance += transaction.transaction_amount
                else:
                    balance -= transaction.transaction_amount
            else:
                pass
        return balance

    def savings_sub_account_balance(self):
        transactions = Transaction.objects.filter(first_partie_bank_account=self).filter(Q(transaction_date__lte=timezone.now()))
        balance = 0.0
        for transaction in transactions:
            if transaction.first_partie_type_of_sub_account == 'SAVINGS':
                if transaction.creditDebitType == 'CREDIT':
                    balance += transaction.transaction_amount
                else:
                    balance -= transaction.transaction_amount
            else:
                pass
        return balance

    def __str__(self):
        return f'Name: {self.customer.name}, CPF: {self.customer.cpf}, Acc.Nº: {self.account_number}, Br.Nº: {self.branch_number}'

class Transaction(models.Model):
    CHECKING = 'CHECKING'
    SAVINGS = 'SAVINGS'
    SUB_ACCOUNT_CHOICES = (
        (CHECKING, 'Checking Account'),
        (SAVINGS, 'Savings Account'),
    )

    CREDIT = 'CREDIT'
    DEBIT = 'DEBIT'
    CREDIT_DEBIT_INDICATOR = (
        (CREDIT, 'Crédito no Extrato'),
        (DEBIT, 'Débito no Extrato')
    )

    transaction_id = models.BigAutoField(primary_key=True)

    # Como é só um MVP, usa-se floats para valor de transação
    # mas o certo é usar um integer cuja visualização é com vírgula
    transaction_amount = models.FloatField()
    creditDebitType = models.TextField(choices=CREDIT_DEBIT_INDICATOR, default=DEBIT)

    transaction_description = models.TextField()
    transaction_date = models.DateTimeField(default=timezone.now())

    first_partie_bank_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='first_partie')
    first_partie_type_of_sub_account = models.TextField(choices=SUB_ACCOUNT_CHOICES, default=CHECKING)

    # Não achamos necessário para o MVP implementar a terceira pessoa da transação
    # third_partie_bank_name = ...
    # third_partie_bank_branch_number = ...
    # third_partie_bank_account_number = ...
    # third_partie_type_of_sub_account
    # third_partie_cpf = ...

    def __str__(self):
        return f'''{self.creditDebitType}, 
        ${self.transaction_amount}, 
        Name: {self.first_partie_bank_account.customer.name}, 
        CPF: {self.first_partie_bank_account.customer.cpf}, 
        Acc.Nº: {self.first_partie_bank_account.account_number}, 
        Br.Nº: {self.first_partie_bank_account.branch_number}'''
