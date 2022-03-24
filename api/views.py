from authlib.integrations.django_oauth2 import ResourceProtector, BearerTokenValidator
from django.http import JsonResponse
from oauth.models import OAuth2Token

from api.models import BankAccount

require_oauth = ResourceProtector()
require_oauth.register_token_validator(BearerTokenValidator(OAuth2Token))

@require_oauth()
def account_balances(request):
    customer = request.oauth_token.user
    bank_account = BankAccount.objects.filter(customer=customer).first()

    response = {}
    response['data'] = {}
    response['data']['availableAmount_CHECKING'] = bank_account.checking_sub_account_balance()
    response['data']['availableAmount_SAVINGS'] = bank_account.savings_sub_account_balance()

    return JsonResponse(response, status=201)