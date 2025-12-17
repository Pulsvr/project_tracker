from django.urls import path
from searches.views import *

urlpatterns = [
    path('', search, name='search'),
]
