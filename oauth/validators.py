from pydoc import cli
from authlib.integrations.django_oauth2 import BearerTokenValidator as _BearerTokenValidator
from authlib.oauth2.rfc6750.errors import (
    InvalidTokenError,
    InsufficientScopeError
)
from oauth.models import OAuth2UserConsent, OAuth2Client

class BearerTokenValidator(_BearerTokenValidator):
    def validate_token(self, token, scopes, request):
        """Check if token is active and matches the requested scopes."""
        if not token:
            raise InvalidTokenError(realm=self.realm, extra_attributes=self.extra_attributes)
        user = token.user
        client = OAuth2Client.objects.filter(client_id=token.client_id).first()
        consent = OAuth2UserConsent.objects.filter(user=user, client=client).first()

        if consent == None:
            raise Exception("Consent object was deleted")
        if consent.is_expired():
            raise Exception("Consent is expired")
        if not consent.is_authorised():
            raise Exception("Consent wasn't authorised")
        # if token.is_expired():
        #     raise InvalidTokenError(realm=self.realm, extra_attributes=self.extra_attributes)
        # if token.is_revoked():
        #     raise InvalidTokenError(realm=self.realm, extra_attributes=self.extra_attributes)
        if self.scope_insufficient(token.get_scope(), scopes):
            raise InsufficientScopeError()