from api.models import Customer
from django.db.models.signals import post_save
from django.dispatch import receiver

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