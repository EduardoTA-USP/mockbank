from django.contrib import admin
from .models import BankAccount, Transaction

class BankAccountAdmin(admin.ModelAdmin):
    list_display = ('account_number','get_balance')

# Register your models here.
admin.site.register(BankAccount, BankAccountAdmin)
admin.site.register(Transaction)
