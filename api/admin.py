from csv import list_dialects
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import BankAccount, Transaction, Customer
from django.utils.translation import gettext, gettext_lazy as _

class BankAccountAdmin(admin.ModelAdmin):
    list_display = ('customer', 'account_number', 'branch_number','checking_sub_account_balance', 'savings_sub_account_balance')

class BankAccountAdminInline(admin.TabularInline):
    model = BankAccount

    fields = ('account_number', 'branch_number', 'checking_sub_account_balance', 'savings_sub_account_balance')
    readonly_fields = ('checking_sub_account_balance', 'savings_sub_account_balance')

class CustomerAdmin(UserAdmin):
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('cpf', 'username', 'name', 'password1', 'password2', 'phone_number'),
        }),
    )

    list_display = ('customer_id', 'cpf', 'name')

    fieldsets = (
        (None, {'fields': (
            'customer_id',
            'cpf',
            'username',
            'name',
            'phone_number')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        #(_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    readonly_fields = ['customer_id']

    inlines = [BankAccountAdminInline,]
    
class TransactionAdmin(admin.ModelAdmin):
    model = Transaction

    list_select_related = ('first_partie_bank_account','first_partie_bank_account__customer')

    list_display = (
        'first_partie_bank_account_cpf',
        'first_partie_bank_account_account_number',
        'first_partie_bank_account_branch_number',
        'first_partie_type_of_sub_account',
        'get_net_amount',
        'transaction_description',
        'transaction_date'
    )

    @admin.display(description = 'CPF')
    def first_partie_bank_account_cpf(self, obj):
        return f"{obj.first_partie_bank_account.customer.cpf}"
    
    @admin.display(description = 'Acc N°')
    def first_partie_bank_account_account_number(self, obj):
        return f"{obj.first_partie_bank_account.account_number}"

    @admin.display(description = 'Br N°')
    def first_partie_bank_account_branch_number(self, obj):
        return f"{obj.first_partie_bank_account.branch_number}"

    @admin.display(description = 'Net Amount')
    def get_net_amount(self, obj):
        creditDebitType = obj.creditDebitType
        if creditDebitType == 'CREDIT':
            amount = obj.transaction_amount
        else:
            amount = -obj.transaction_amount
        return f"{amount}"

# Register your models here.
admin.site.register(BankAccount, BankAccountAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Customer, CustomerAdmin)