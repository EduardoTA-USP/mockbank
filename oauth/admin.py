from django.contrib import admin
from .models import OAuth2Client, OAuth2Code, OAuth2Token, OAuth2UserConsent

# Register your models here.
class OAuth2ClientAdmin(admin.ModelAdmin):
    list_display = ('user', 'client_name')
    readonly_fields = ('client_id', 'client_secret')

admin.site.register(OAuth2Client, OAuth2ClientAdmin)
admin.site.register(OAuth2Token)
admin.site.register(OAuth2Code)
admin.site.register(OAuth2UserConsent)