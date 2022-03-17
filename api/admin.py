from django.contrib import admin
from .models import BankAccount, Transaction, Customer

class BankAccountAdmin(admin.ModelAdmin):
    list_display = ('account_number','checking_sub_account_balance', 'savings_sub_account_balance')

class CustomerAdmin(admin.ModelAdmin):
    list_display = ('customer_id', 'name', 'cpf', 'phone_number')
    readonly_fields = ['customer_id']


# Register your models here.
admin.site.register(BankAccount, BankAccountAdmin)
admin.site.register(Transaction)
admin.site.register(Customer, CustomerAdmin)