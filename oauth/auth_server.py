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
from .grants import ( AuthorizationCodeGrant, ImplicitGrant )

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
    
    def save_token(self, token, request):
        client = request.client
        if request.user:
            user_id = request.user.pk
        else:
            user_id = client.user_id
        item = self.token_model.objects.filter(user=request.user, client_id=client.client_id).first()

        if item != None:
            item.delete()
            
        item = self.token_model(
            client_id=client.client_id,
            user_id=user_id,
            **token
        )
        item.save()
        return item
        
server = AuthorizationServer(OAuth2Client, OAuth2Token)
server.register_grant(AuthorizationCodeGrant)
server.register_grant(ImplicitGrant)