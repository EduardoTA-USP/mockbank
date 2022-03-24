from oauth.models import OAuth2UserConsent
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from mockbank.settings import BANK_NAME

import secrets
def random_gen():
    return secrets.token_urlsafe(nbytes=8)

def generate_and_update_consent_id(consent):
    got_unique_consent_id = False
    while got_unique_consent_id == False:
        generated_consent_id = f'urn:{BANK_NAME}:{random_gen()}'
        if OAuth2UserConsent.objects.filter(consent_id=generated_consent_id):
            got_unique_consent_id = False
        else:
            got_unique_consent_id = True
            consent.update(consent_id=generated_consent_id) 
            return True

@receiver(post_save, sender=OAuth2UserConsent)
def post_save_create_consent_id(sender, instance, created, **kwargs):
    consent = OAuth2UserConsent.objects.filter(pk=str(instance.pk))
    if consent.first().consent_id == None:
        generate_and_update_consent_id(consent)