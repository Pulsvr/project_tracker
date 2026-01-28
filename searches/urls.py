from django.urls import path
from searches.views import *

urlpatterns = [
    path('', search, name='search'),
    path('create/', create_search, name='create_search'),
    path('<int:id>/', detail_search, name='detail_search'),
]
