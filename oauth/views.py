import time
from django.shortcuts import render
# Create your views here.
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .auth_server import server
from authlib.oauth2.rfc6749.util import scope_to_list, list_to_scope

from django.template import loader
from django.http import Http404, HttpResponse

from django.contrib.auth.decorators import login_required

from .models import OAuth2UserConsent
from django.conf import settings 

from django.views.decorators.csrf import csrf_exempt

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
