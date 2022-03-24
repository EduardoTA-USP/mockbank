from django.urls import path, include
from .views import authorize, issue_token, consents

urlpatterns = [
    path('auth/', authorize, name='authorize'),
    path('token/', issue_token, name='issue_token'),
    path('consents/consents/', consents, name='consents'),
    path('consents/consents/<str:consent_id>/', consents, name='consents'),
]