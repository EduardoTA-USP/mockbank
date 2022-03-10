from django.urls import path, include
from .views import authorize, issue_token

urlpatterns = [
    path('authorize/', authorize, name='authorize'),
    path('token/', issue_token, name='issue_token')
]