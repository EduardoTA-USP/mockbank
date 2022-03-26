from django.urls import path, include
from .views import authorize, issue_token, consents_dispatcher

urlpatterns = [
    path('auth/', authorize, name='authorize'),
    path('token/', issue_token, name='issue_token'),
    path('consents/consents/', consents_dispatcher, name='consents_dispatcher'),
    path('consents/consents/<str:consent_id>/', consents_dispatcher, name='consents_dispatcher'),
]