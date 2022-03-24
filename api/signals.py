from datetime import datetime
from api.models import Transaction, BankAccount, Customer
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.db.models import Q

from django.utils import timezone

# def update_balance(bank_account: BankAccount):
#     transactions = Transaction.objects.filter(first_partie_bank_account=bank_account).filter(Q(transaction_date__lte=timezone.now()))

#     checking_sub_account_balance = 0.0
#     savings_sub_account_balance = 0.0
#     for transaction in transactions:
#         if transaction.first_partie_type_of_sub_account == 'CHECKING':
#             checking_sub_account_balance += transaction.transaction_amount
#         elif transaction.first_partie_type_of_sub_account == 'SAVINGS':
#             savings_sub_account_balance += transaction.transaction_amount
#         else:
#             raise(f'Invalid type of sub-account {transaction.first_partie_type_of_sub_account}')
    
#     bank_account_object = BankAccount.objects.filter(account_id = bank_account.account_id)
#     bank_account_object.update(checking_sub_account_balance=checking_sub_account_balance)  
#     bank_account_object.update(savings_sub_account_balance=savings_sub_account_balance)  

# @receiver(pre_delete, sender=Transaction)
# def pre_delete_update_balance(sender, instance, **kwargs):
#     bank_account = instance.first_partie_bank_account
#     transaction = Transaction.objects.filter(pk=str(instance.pk))
#     transaction.update(transaction_amount=0.0)
#     update_balance(bank_account)

# @receiver(post_save, sender=Transaction)
# def post_save_update_balance(sender, instance, created, **kwargs):
#     bank_account = instance.first_partie_bank_account
#     update_balance(bank_account)

import secrets
def random_gen():
    return secrets.token_urlsafe(nbytes=16)

@receiver(post_save, sender=Customer)
def post_save_create_customer_id(sender, instance, created, **kwargs):
    customer = Customer.objects.filter(pk=str(instance.pk))
    if customer.first().customer_id == None:
        got_unique_customer_id = False
        while got_unique_customer_id == False:
            generated_customer_id = f'{random_gen()}'
            if Customer.objects.filter(customer_id=generated_customer_id):
                got_unique_customer_id = False
            else:
                got_unique_customer_id = True
                customer.update(customer_id=generated_customer_id)