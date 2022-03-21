from django.utils.module_loading import import_string
from authlib.oauth2 import OAuth2Request
from authlib.oauth2.rfc6749.grants import ClientCredentialsGrant
from authlib.integrations.django_oauth2 import (
    AuthorizationServer as _AuthorizationServer,
    RevocationEndpoint,
)

from authlib.integrations.django_helpers import create_oauth_request

from . import models, grants

from .models import ( OAuth2Client, OAuth2Token )
from .grants import ( AuthorizationCodeGrant )

class AuthorizationServer(_AuthorizationServer):
    def create_oauth2_request(self, request):
        content_type = request.content_type
        if content_type:
            # In case of 'application/json; indent=4'
            content_type = content_type.split(';')[0]
        use_json = 'application/json' == content_type
        oauth2_request = create_oauth_request(request, OAuth2Request, use_json=use_json)
        oauth2_request.integration_request = request
        return oauth2_request
        
server = AuthorizationServer(OAuth2Client, OAuth2Token)
server.register_grant(AuthorizationCodeGrant)