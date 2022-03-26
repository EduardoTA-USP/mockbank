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

    consent_id = re.findall('(?<=consent:)\S*', request.GET['scope'])
    scope = request.GET['scope'].split()
    regex = re.compile("consent\:.*")
    for index, item in enumerate(scope):
        if re.search(regex, item):
            consent_id = item
    scope.remove(consent_id)

    scope = client.get_allowed_scope(scope)

    if request.method == 'GET':
        # TODO: verificar se os parâmetros fornecidos na query dão match com o consent referenciado por consent_id
        if client_has_user_consent(client, request.user, scope):
            # skip consent and granted
            return server.create_authorization_response(request, grant_user=request.user)
        context = dict(grant=grant, client=client, scope=request.GET['scope'], user=request.user)
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

# Consent create
# TODO: client_credentials client authentication for route
@csrf_exempt # TODO: CSRF protection with token
def consents(request, consent_id=None):
    if request.method == 'POST':
        try:
            json_data = json.loads(str(request.body, encoding='utf-8'))
            user_cpf = json_data['data']['loggedUser']['document']['identification']

            permissions = json_data['data']['permissions']

            expires_at = json_data['data']['expirationDateTime']
            expires_at = re.sub('T', ' ', expires_at)
            expires_at = re.sub('Z', '+00:00', expires_at)
            expires_at = datetime.datetime.fromisoformat(expires_at)

            client_id = json_data['data']['client_id']
            client_secret = json_data['data']['client_secret']
        except:
            return JsonResponse({'message': 'Malformed request body'}, status=400)

        user = Customer.objects.filter(cpf=user_cpf).first() 
        client = OAuth2Client.objects.filter(client_id=client_id).first()

        if user == None:
            return JsonResponse({'message': 'User with suplied cpf not found'}, status=404)
        if client == None:
            return JsonResponse({'message': 'Invalid consent_id'}, status=404)
        
        if timezone.now() >= expires_at:
            return JsonResponse({'message': 'Invalid expiration datetime'}, status=400)

        if getattr(client, 'client_secret', None) != client_secret:
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
            client_id = json_data['data']['client_id']
            client_secret = json_data['data']['client_secret']
        except:
            return JsonResponse({'message': 'Malformed request body'}, status=400)

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
        
        response = {}
        response['data'] = {}
        response['data']['consentId'] = consent.consent_id
        response['data']['creationDateTime'] = consent.created_at
        response['data']['status'] = consent.status
        response['data']['statusUpdateDateTime'] = consent.status_updated_at
        response['data']['permissions'] = consent.permissions
        response['data']['expirationDateTime'] = consent.expires_at
        return JsonResponse(response, status=200)


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