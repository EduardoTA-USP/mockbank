from authlib.oauth2.rfc6749.grants import (
    AuthorizationCodeGrant as _AuthorizationCodeGrant, AuthorizationEndpointMixin, TokenEndpointMixin,
    ImplicitGrant as _ImplicitGrant
)
from authlib.oauth2.rfc6749.errors import (
    InvalidClientError, UnauthorizedClientError, AccessDeniedError
)
from authlib.oauth2.base import OAuth2Error
from authlib.common.urls import add_params_to_uri
from .models import OAuth2Client, OAuth2Code

from django.http import JsonResponse
import re

class AuthorizationCodeGrant(_AuthorizationCodeGrant):
    TOKEN_ENDPOINT_AUTH_METHODS = ['none']
    def save_authorization_code(self, code, request):
        client = request.client
        auth_code = OAuth2Code(
            code=code,
            client_id=client.client_id,
            redirect_uri=request.redirect_uri,
            response_type=request.response_type,
            scope=request.scope,
            user=request.user,
        )
        auth_code.save()
        return auth_code

    def query_authorization_code(self, code, client):
        try:
            item = OAuth2Code.objects.get(code=code, client_id=client.client_id)
        except OAuth2Code.DoesNotExist:
            return None

        if not item.is_expired():
            return item

    def delete_authorization_code(self, authorization_code):
        authorization_code.delete()

    def authenticate_user(self, authorization_code):
        return authorization_code.user

    def validate_authorization_request(self):
        request = self.request
        client_id = request.client_id

        if client_id is None:
            raise InvalidClientError(JsonResponse({f'message': 'client_id not present'}, status=401))

        client = self.server.query_client(client_id)
        if not client:
            raise InvalidClientError(JsonResponse({f'message': 'No registered client with client_id={client_id}'}, status=401))

        redirect_uri = self.validate_authorization_redirect_uri(request, client)
        response_type = request.response_type
        if not client.check_response_type(response_type):
            raise UnauthorizedClientError(
                f'The client is not authorized to use "response_type={response_type}"',
                state=self.request.state,
                redirect_uri=redirect_uri,
            )

        try:
            self.request.client = client
            self.validate_requested_scope()
            self.execute_hook('after_validate_authorization_request')
        except OAuth2Error as error:
            error.redirect_uri = redirect_uri
            raise error
        return redirect_uri
    
    def validate_requested_scope(self):
        scope = self.request.scope
        consent_id = re.findall('(?<=consent:)\S*', scope)

        # TODO: Validate consent_id
    
    # def create_authorization_response(self, redirect_uri, grant_user):
    #     if not grant_user:
    #         raise AccessDeniedError(state=self.request.state, redirect_uri=redirect_uri)

    #     self.request.user = grant_user

    #     code = self.generate_authorization_code()
    #     self.save_authorization_code(code, self.request)

    #     params = [('code', code)]
    #     if self.request.state:
    #         params.append(('state', self.request.state))
    #     params.append(('customer_id', self.request.user.customer_id))
    #     uri = add_params_to_uri(redirect_uri, params)
    #     headers = [('Location', uri)]
    #     return 302, '', headers

class ImplicitGrant(_ImplicitGrant):
    def validate_authorization_request(self):
        request = self.request
        
        only_one_client_in_database = request.integration_request.GET.get('only_one_client_in_database', None)
        if only_one_client_in_database == None:
            client_id = request.client_id
        else:
            client_id = OAuth2Client.objects.all().first().client_id

        if client_id is None:
            raise InvalidClientError(JsonResponse({f'message': 'client_id not present or client was deleted'}, status=401))

        client = self.server.query_client(client_id)
        if not client:
            raise InvalidClientError(JsonResponse({f'message': 'No registered client with client_id={client_id}'}, status=401))

        redirect_uri = client.get_default_redirect_uri()
        response_type = request.response_type
        if not client.check_response_type(response_type):
            raise UnauthorizedClientError(
                f'The client is not authorized to use "response_type={response_type}"',
                state=self.request.state,
                redirect_uri=redirect_uri,
            )

        try:
            self.request.client = client
            self.validate_requested_scope()
            self.execute_hook('after_validate_authorization_request')
        except OAuth2Error as error:
            error.redirect_uri = redirect_uri
            raise error
        return redirect_uri
