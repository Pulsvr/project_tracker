from django.urls import path
from searches.views import *

urlpatterns = [
    path('', search, name='search'),
    path('create/', create_search, name='create_search'),
    path('<int:id>/', detail_search, name='detail_search'),
    path('<int:id>/update/', update_search, name='update_search'),
    path('<int:id>/delete/', delete_search, name='delete_search'),
]
