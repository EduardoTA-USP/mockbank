from django.contrib import admin
from .models import BankAccount, Transaction, Customer

class BankAccountAdmin(admin.ModelAdmin):
    # list_display = ('account_number','get_balance')
    pass

class CustomerAdmin(admin.ModelAdmin):
    pass


# Register your models here.
admin.site.register(BankAccount, BankAccountAdmin)
admin.site.register(Transaction)
admin.site.register(Customer, CustomerAdmin)