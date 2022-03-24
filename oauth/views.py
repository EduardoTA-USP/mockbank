import re, datetime, json, secrets
from django.shortcuts import render
# Create your views here.
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .auth_server import server
from authlib.oauth2.rfc6749.util import scope_to_list, list_to_scope

from django.template import loader
from django.http import Http404, HttpResponse

from django.contrib.auth.decorators import login_required

from oauth.models import OAuth2UserConsent, OAuth2Client
from api.models import Customer
from django.conf import settings 

from django.views.decorators.csrf import csrf_exempt

from django.http import JsonResponse

from django.utils import timezone

from oauth.signals import generate_and_update_consent_id

from authlib.oauth2.rfc6749.util import scope_to_list, list_to_scope

# use ``server.create_authorization_response`` to handle authorization endpoint

@login_required
def authorize(request):
    print(request)
    if request.method == 'GET':
        try:
            grant = server.validate_consent_request(request, end_user=request.user)
        except Exception as e:
            raise Http404(e)
        client = grant.client

        # Check if scope in query params is in client's allowed scopes
        if client.get_allowed_scope(grant.request.scope):
            if client_has_user_consent(grant.client, request.user, request.GET['scope']):
                # skip consent and granted
                return server.create_authorization_response(request, grant_user=request.user)
        context = dict(grant=grant, client=client, scope=request.GET['scope'], user=request.user)
        return render(request, 'authorize.html', context)
    if request.method == 'POST':
        if not is_user_consented(request):
            # denied by resource owner
            return server.create_authorization_response(request, grant_user=None)
        try:
            grant = server.validate_consent_request(request, end_user=request.user)
        except Exception as e:
            raise Http404(e)
        scope_list = request.GET['scope']
        set_client_user_consent(grant.client, request.user, list_to_scope(scope_list))

        # granted by resource owner
        return server.create_authorization_response(request, grant_user=request.user)

# use ``server.create_token_response`` to handle token endpoint

@csrf_exempt
@require_http_methods(["POST"])  # we only allow POST for token endpoint
def issue_token(request):
    return server.create_token_response(request)

def login(request):
    template = loader.get_template('login.html')
    return HttpResponse(template.render(None, request))

# Consent create
# TODO: client_credentials client authentication for route
@csrf_exempt # TODO: CSRF protection with token
def consents(request, consent_id=None):
    if request.method == 'POST':
        json_data = json.loads(str(request.body, encoding='utf-8'))

        user_cpf = json_data['data']['loggedUser']['document']['identification']
        user = Customer.objects.filter(cpf=user_cpf).first()

        permissions = json_data['data']['permissions']

        expires_at = json_data['data']['expirationDateTime']
        expires_at = re.sub('T', ' ', expires_at)
        expires_at = re.sub('Z', '+00:00', expires_at)
        expires_at = datetime.datetime.fromisoformat(expires_at)

        client_id = json_data['data']['client_id']
        client_secret = json_data['data']['client_secret']
        client = OAuth2Client.objects.filter(client_id=client_id).first()

        if getattr(OAuth2Client.objects.filter(client_id=client_id).first(), 'client_secret', None) == client_secret:
            consent, created = OAuth2UserConsent.objects.update_or_create(
                user=user, client=client,
                defaults={
                    'consent_id': secrets.token_urlsafe(nbytes=8),
                    'permissions': permissions,
                    'expires_at': expires_at,
                    'created_at': timezone.now(),
                    'given_at': None,
                    'status': 'AWAITING_AUTHORISATION' }
            )

            # É mais fácil trabalhar com a queryset do que o objeto em si
            consent_query_set = OAuth2UserConsent.objects.filter(id=consent.id)

            if not created:
                generate_and_update_consent_id(consent_query_set)

            response = {}
            response['data'] = {}
            response['data']['consentId'] = consent_query_set.first().consent_id
            response['data']['creationDateTime'] = consent_query_set.first().created_at
            response['data']['status'] = consent_query_set.first().status
            response['data']['permissions'] = consent_query_set.first().permissions
            response['data']['expirationDateTime'] = consent_query_set.first().expires_at
            response['links'] = {}

            # Builds authorization request URI
            response['links']['self'] = f'{request._current_scheme_host}/consents/{consent_query_set.first().consent_id}'

            return JsonResponse(response, status=201)
        else:
            return JsonResponse({'message': 'client authentication failed, check client_id or client_secret'}, status=401)
            
    if request.method == 'GET':
        # TODO: get consent info
        return 0
    
    if request.method == 'DELETE':
        # TODO: delete consent
        return 0

def client_has_user_consent(client, user, scope):
    try:
        uc = OAuth2UserConsent.objects.get(client=client, user=user)
        return uc.contains_scope(scope) and not uc.is_expired()
    except OAuth2UserConsent.DoesNotExist:
        return False

def is_user_consented(request):
    return request.POST.get('action') == 'consent'

def set_client_user_consent(client, user, scope):
    given_at = int(time.time())
    expires_in = getattr(settings, 'OAUTH2_SKIP_CONSENT_EXPIRES_IN', 86400)

    uc, created = OAuth2UserConsent.objects.get_or_create(
        client=client, user=user,
        defaults={
            'given_at': given_at,
            'expires_in': expires_in,
            'scope': scope,
        },
    ) 

    if not created:
        uc.given_at = given_at
        uc.expires_in = expires_in
        uc.scope = scope
        uc.save()
