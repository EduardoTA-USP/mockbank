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

# User consent approval view
@login_required
def authorize(request):
    try:
        grant = server.get_consent_grant(request=request, end_user=request.user)
    except Exception as e:
        raise Http404(e)
    client = grant.client

    try:
        consent_id = re.findall('(?<=consent:)\S*', request.GET['scope'])
    except:
        consent_id = None
        print("WARNING: Authorization request without consent_id")
    try:
        scope = request.GET['scope'].split()
    except:
        # If no scope is suplied, use the default
        scope = ['accounts']
    regex = re.compile("consent\:.*")
    for index, item in enumerate(scope):
        if re.search(regex, item):
            consent_id = item
    if consent_id:
        scope.remove(consent_id)

    scope = client.get_allowed_scope(scope)

    if consent_id == None:
        consent = OAuth2UserConsent.objects.filter(user=request.user, client=grant.client).first()
    else:
        consent = OAuth2UserConsent.objects.filter(consent_id=consent_id, user=request.user, client=grant.client).first()
    
    is_consent_invalid = consent == None or getattr(consent, 'status', None) == 'REJECTED' or getattr(consent, 'is_expired', None)()
    if is_consent_invalid:
        return server.create_authorization_response(request, grant_user=None)

    if request.method == 'GET':
        if client_has_user_consent(client, request.user, scope):
            # skip consent and granted
            return server.create_authorization_response(request, grant_user=request.user)
        context = dict(grant=grant, client=client, scope=scope, consent=consent, user=request.user)
        return render(request, 'authorize.html', context)
    if request.method == 'POST':
        if not is_user_consented(request):
            OAuth2UserConsent.objects.filter(user=request.user, client=grant.client).update(status='REJECTED')           
            OAuth2UserConsent.objects.filter(user=request.user, client=grant.client).update(status_updated_at=timezone.now())           

            # denied by resource owner
            return server.create_authorization_response(request, grant_user=None)

        set_client_user_consent(grant.client, request.user, list_to_scope(scope))

        # granted by resource owner
        return server.create_authorization_response(request, grant_user=request.user)

# use ``server.create_token_response`` to handle token endpoint

# Access Token request view
@csrf_exempt # TODO: CSRF protection with token
@require_http_methods(["POST"])  # we only allow POST for token endpoint
def issue_token(request):
    return server.create_token_response(request)

# TODO: Login view
def login(request):
    template = loader.get_template('login.html')
    return HttpResponse(template.render(None, request))

@csrf_exempt
def consents_dispatcher(request, consent_id=None):
    if request.method in ["POST", "GET"]:
        return consents_get_post(request, consent_id=consent_id)
    else:
        return consents_delete(request, consent_id=consent_id)

# Consent create
# TODO: client_credentials client authentication for route
@csrf_exempt # TODO: CSRF protection with token
@require_http_methods(["POST", "GET"])
def consents_get_post(request, consent_id=None):
    if request.method == 'POST':
        try:
            json_data = json.loads(str(request.body, encoding='utf-8'))
            user_cpf = json_data['data']['loggedUser']['document']['identification']

            permissions = json_data['data']['permissions']

            expires_at = json_data['data']['expirationDateTime']
            expires_at = re.sub('T', ' ', expires_at)
            expires_at = re.sub('Z', '+00:00', expires_at)
            expires_at = datetime.datetime.fromisoformat(expires_at)

            only_one_client_in_database = json_data['data'].get('only_one_client_in_database', None)

            if only_one_client_in_database == None:
                client_id = json_data['data']['client_id']
                client_secret = json_data['data']['client_secret']
        except:
            return JsonResponse({'message': 'Malformed request body'}, status=400)

        user = Customer.objects.filter(cpf=user_cpf).first()
        if only_one_client_in_database == None:
            client = OAuth2Client.objects.filter(client_id=client_id).first()
        else:
            client = OAuth2Client.objects.all().first()

        if user == None:
            return JsonResponse({'message': 'User with suplied cpf not found'}, status=404)
        if client == None:
            return JsonResponse({'message': 'Invalid client_id or no client registered'}, status=404)
        
        if timezone.now() >= expires_at:
            return JsonResponse({'message': 'Invalid expiration datetime'}, status=400)

        if only_one_client_in_database == None and getattr(client, 'client_secret', None) != client_secret:
            return JsonResponse({'message': 'client authentication failed, check client_id or client_secret'}, status=401)
        
        consent, created = OAuth2UserConsent.objects.update_or_create(
            user=user, client=client,
            defaults={
                'consent_id': secrets.token_urlsafe(nbytes=8),
                'scope': None,
                'status_updated_at': timezone.now(),
                'expires_at': expires_at,
                'created_at': timezone.now(),
                'permissions': permissions,
                'status': 'AWAITING_AUTHORISATION' }
        )

        # É mais fácil trabalhar com a queryset do que o objeto em si
        consent_query_set = OAuth2UserConsent.objects.filter(id=consent.id)

        generate_and_update_consent_id(consent_query_set)

        response = {}
        response['data'] = {}
        response['data']['consentId'] = consent_query_set.first().consent_id
        response['data']['creationDateTime'] = consent_query_set.first().created_at
        response['data']['status'] = consent_query_set.first().status
        response['data']['statusUpdateDateTime'] = consent_query_set.first().status_updated_at
        response['data']['permissions'] = consent_query_set.first().permissions
        response['data']['expirationDateTime'] = consent_query_set.first().expires_at

        return JsonResponse(response, status=201)
            
    if request.method == 'GET':
        try:
            json_data = json.loads(str(request.body, encoding='utf-8'))

            # User CPF as an alternative to consent_id
            user_cpf = json_data['data'].get('user_cpf', None)
            only_one_client_in_database = json_data['data'].get('only_one_client_in_database', None)

            if user_cpf == None and only_one_client_in_database == None:
                client_id = json_data['data']['client_id']
                client_secret = json_data['data']['client_secret']
        except:
            return JsonResponse({'message': 'Malformed request body'}, status=400)

        if user_cpf == None and only_one_client_in_database == None:
            client = OAuth2Client.objects.filter(client_id=client_id).first()
            if client == None:
                return JsonResponse({'message': 'Invalid client_id'}, status=401)

            if getattr(client, 'client_secret', None) != client_secret:
                return JsonResponse({'message': 'client authentication failed, check client_id or client_secret'}, status=401)

            consent = OAuth2UserConsent.objects.filter(consent_id=consent_id).first()
            if consent == None:
                return JsonResponse({'message': 'Invalid consent_id'}, status=404)

            if getattr(consent, 'client', None) != client:
                return JsonResponse({'message': 'Request\'s client_id dosen\'t match consent\'s client_id'}, status=401)
        else:
            # User CPF as an alternative to consent_id
            user = Customer.objects.filter(cpf=user_cpf).first()
            if user == None:
                return JsonResponse({'message': 'User with suplied cpf not found'}, status=404)
            consent = OAuth2UserConsent.objects.filter(user=user).first()
            if consent == None:
                return JsonResponse({'message': 'No consent object was found'}, status=404)
        
        response = {}
        response['data'] = {}
        response['data']['consentId'] = consent.consent_id
        response['data']['creationDateTime'] = consent.created_at
        response['data']['status'] = consent.status
        response['data']['statusUpdateDateTime'] = consent.status_updated_at
        response['data']['permissions'] = consent.permissions
        response['data']['expirationDateTime'] = consent.expires_at
        return JsonResponse(response, status=200)

from authlib.integrations.django_oauth2 import ResourceProtector, BearerTokenValidator
from oauth.models import OAuth2Token
require_oauth = ResourceProtector()
require_oauth.register_token_validator(BearerTokenValidator(OAuth2Token))

@csrf_exempt # TODO: CSRF protection with token
#@require_oauth()
@require_http_methods(["DELETE"])
def consents_delete(request, consent_id=None):
    try:
        json_data = json.loads(str(request.body, encoding='utf-8'))
         # User CPF as an alternative to consent_id
        user_cpf = json_data['data'].get('user_cpf', None)
        only_one_client_in_database = json_data['data'].get('only_one_client_in_database', None)

        if user_cpf == None and only_one_client_in_database == None:
            client_id = json_data['data']['client_id']
            client_secret = json_data['data']['client_secret']
    except:
        return JsonResponse({'message': 'Malformed request body'}, status=400)

    if user_cpf == None and only_one_client_in_database == None:
        if client_id != request.oauth_token.client_id:
            return JsonResponse({'message': 'Wrong client_id'}, status=401)
    else:
        client_id = request.oauth_token.client_id

    client = OAuth2Client.objects.filter(client_id=client_id).first()
    if client == None:
        return JsonResponse({'message': 'Client was deleted'}, status=404)

    if user_cpf == None and only_one_client_in_database == None:
        if getattr(client, 'client_secret', None) != client_secret:
            return JsonResponse({'message': 'client authentication failed, check client_id or client_secret'}, status=401)

    user = request.oauth_token.user
    if user_cpf != None and user.cpf != user_cpf:
        return JsonResponse({'message': 'Suplied user_cpf doesn\'t match access token\'s user'}, status=401)

    if user_cpf == None and only_one_client_in_database == None:
        consent = OAuth2UserConsent.objects.filter(consent_id=consent_id, user=user, client=client).first()
    else:
        consent = OAuth2UserConsent.objects.filter(user=user, client=client).first()

    if consent == None:
        return JsonResponse({'message': 'This consent object doesn\'t exist'}, status=404)
    OAuth2UserConsent.objects.filter(consent_id=consent.consent_id, user=user, client=client).delete()


    return JsonResponse({'message': 'Consent successfully deleted'}, status=204)


def client_has_user_consent(client, user, scope):
    try:
        user_consent = OAuth2UserConsent.objects.get(client=client, user=user)
        return user_consent.contains_scope(scope) and not user_consent.is_expired() and user_consent.is_authorised()
    except OAuth2UserConsent.DoesNotExist:
        return False

def is_user_consented(request):
    return request.POST.get('action') == 'consent'

def set_client_user_consent(client, user, scope):
    status_updated_at = timezone.now()

    OAuth2UserConsent.objects.filter(client=client, user=user).update(
        status_updated_at = status_updated_at,
        status = 'AUTHORISED',
        scope = scope
    )