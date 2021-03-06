import time, re
from datetime import datetime
from xmlrpc import client
from api.models import Customer as User
from django.db import models

from authlib.oauth2.rfc6749 import ClientMixin, TokenMixin
from authlib.oauth2.rfc6749 import AuthorizationCodeMixin
from authlib.oauth2.rfc6749.util import scope_to_list, list_to_scope

from django.utils.crypto import get_random_string
from django.utils.functional import cached_property

from django.utils import timezone
from django.core.exceptions import ValidationError

CLIENT_ID_LENGTH = 32
CLIENT_SECRET_LENGTH = 48

DEFAULT_TOKEN_EXPIRATION_SECONDS = 3600

GRANT_AUTHORIZATION_CODE = "authorization_code"
GRANT_IMPLICIT = "implicit"
SUPPORTED_GRANT_TYPES = [GRANT_AUTHORIZATION_CODE, GRANT_IMPLICIT]

RESPONSE_TYPE_CODE = "code"
RESPONSE_TYPE_TOKEN = "token"
SUPPORTED_RESPONSE_TYPES = [RESPONSE_TYPE_CODE, RESPONSE_TYPE_TOKEN]

SCOPE_ACCOUNTS = "accounts"
SUPPORTED_SCOPES = [SCOPE_ACCOUNTS]

CLIENT_AUTH_METHOD_NONE = "none"
SUPPORTED_CLIENT_AUTH_METHODS = [CLIENT_AUTH_METHOD_NONE]

def generate_client_id():
    return get_random_string(
        length=CLIENT_ID_LENGTH,
        allowed_chars="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
    )

def generate_client_secret():
    return get_random_string(
        length=CLIENT_SECRET_LENGTH,
        allowed_chars=(
            "abcdefghijklmnopqrstuvwxyz"
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "0123456789"
            "!#$*()[]{}"
        ),
    )

def now_timestamp():
    return int(time.time())

class OAuth2Client(models.Model, ClientMixin):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    client_id = models.CharField(default='', max_length=48, unique=True, db_index=True, editable=False)
    client_secret = models.CharField(default='', max_length=48, blank=True, editable=False)
    client_name = models.CharField(max_length=120)
    default_redirect_uri = models.TextField(default='')
    redirect_uri = models.TextField(default='', editable=False)
    scope = models.TextField(default=SCOPE_ACCOUNTS)
    response_type = models.TextField(default=RESPONSE_TYPE_CODE)
    grant_type = models.TextField(default=GRANT_AUTHORIZATION_CODE)
    token_endpoint_auth_method = models.CharField(max_length=120, default=CLIENT_AUTH_METHOD_NONE, editable=False)

    # you can add more fields according to your own need
    # check https://tools.ietf.org/html/rfc7591#section-2

    def get_client_id(self):
        return self.client_id

    def get_default_redirect_uri(self):
        return self.default_redirect_uri

    def get_allowed_scope(self, scope):
        if not scope:
            return ''
        allowed = set(scope_to_list(self.scope))
        return list_to_scope([s for s in scope if s in allowed])

    def check_redirect_uri(self, redirect_uri):
        return redirect_uri == self.redirect_uri

    def has_client_secret(self):
        return bool(self.client_secret)

    def check_client_secret(self, client_secret):
        return self.client_secret == client_secret

    def check_token_endpoint_auth_method(self, method):
        return True

    def check_endpoint_auth_method(self, method, endpoint):
        if endpoint == 'token':
          return self.token_endpoint_auth_method == method
        # TODO: developers can update this check method
        return True

    def check_response_type(self, response_type):
        allowed = self.response_type.split()
        return response_type in allowed

    def check_grant_type(self, grant_type):
        allowed = self.grant_type.split()
        return grant_type in allowed
    
    def clean_fields(self, *args, **kwargs):
        for scope in self.scope.split():
            if not(scope in SUPPORTED_SCOPES):
                raise ValidationError({'scope': [f"scope {scope} is not supported"]})
        for grant in self.grant_type.split():
            if not(grant in SUPPORTED_GRANT_TYPES):
                raise ValidationError({'grant_type': [f"grant_type {grant} is not supported"]})
        for response_type in self.response_type.split():
            if not(response_type in SUPPORTED_RESPONSE_TYPES):
                raise ValidationError({'response_type': [f"response_type {response_type} is not supported"]})
        
        super(OAuth2Client, self).clean_fields(*args, **kwargs)

    def save(self, *args, **kwargs):
        if self.client_id == '':
            self.client_id = generate_client_id()
        if self.client_secret == '':
            self.client_secret = generate_client_secret()
        self.redirect_uri = self.default_redirect_uri
        super(OAuth2Client, self).save(*args, **kwargs)
    
    class Meta:
        verbose_name = "OAuth2 Client"
        verbose_name_plural = "OAuth2 Clients"
    
    def __str__(self):
        return f"Name: {self.client_name}"


class OAuth2Token(models.Model, TokenMixin):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    client_id = models.CharField(max_length=48, db_index=True)
    token_type = models.CharField(max_length=40)
    access_token = models.CharField(max_length=255, unique=True, null=False)
    refresh_token = models.CharField(max_length=255, db_index=True)
    scope = models.TextField(default='')
    revoked = models.BooleanField(default=False)
    issued_at = models.IntegerField(null=False, default=now_timestamp)
    expires_in = models.IntegerField(null=False, default=100000000)

    def get_client_id(self):
        return self.client_id

    def get_scope(self):
        return self.scope

    def get_expires_in(self):
        return self.expires_in

    def get_expires_at(self):
        return self.issued_at + self.expires_in

    def is_expired(self):
        return self.get_expires_at() < now_timestamp()
    
    def is_revoked(self):
        return False
    
    class Meta:
        verbose_name = "OAuth2 Access Token"
        verbose_name_plural = "OAuth2 Access Tokens"
    
    def __str__(self):
        return f"From user: {self.user}, To client: {OAuth2Client.objects.filter(client_id=self.client_id).first().client_name}"

class OAuth2Code(models.Model, AuthorizationCodeMixin):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    client_id = models.CharField(max_length=48, db_index=True)
    code = models.CharField(max_length=120, unique=True, null=False)
    redirect_uri = models.TextField(default='', null=True)
    response_type = models.TextField(default='')
    scope = models.TextField(default='', null=True)
    auth_time = models.IntegerField(null=False, default=now_timestamp)

    def is_expired(self):
        # TODO: Colocar um tempo realista para validade de c??digo de autoriza????o
        return self.auth_time + 30000000 < time.time()

    def get_redirect_uri(self):
        return self.redirect_uri

    def get_scope(self):
        return self.scope or ''

    def get_auth_time(self):
        return self.auth_time
    
    class Meta:
        verbose_name = "OAuth2 Authorization Code"
        verbose_name_plural = "OAuth2 Authorization Codes"

CONSENT_STATUS_CHOICES = (
    ('AWAITING_AUTHORISATION', 'AWAITING_AUTHORISATION'),
    ('AUTHORISED', 'AUTHORISED'),
    ('REJECTED', 'REJECTED'),
)

class OAuth2UserConsent(models.Model):
    consent_id = models.TextField(editable=False, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    client = models.ForeignKey(OAuth2Client, on_delete=models.CASCADE)
    scope = models.TextField(null=True, blank=True)
    status_updated_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(null=True)
    permissions = models.JSONField(null=True)
    status = models.TextField(choices=CONSENT_STATUS_CHOICES, default='AWAITING_AUTHORISATION')

    #@cached_property
    def status_updated_at_time(self):
        return self.status_updated_at

    @cached_property
    def expires_at_time(self):
        return self.expires_at
    
    def is_expired(self):
        return self.expires_at < timezone.now()
    
    def is_authorised(self):
        return True if self.status == 'AUTHORISED' else False
    
    def contains_scope(self, scope):
        had = scope_to_list(scope)
        needed = set(scope_to_list(scope))
        return needed.issubset(had)
    
    class Meta:
        verbose_name = "OAuth2 User Consent"
        verbose_name_plural = "OAuth2 User Consents"