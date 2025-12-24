from django.urls import path
from users.views import *


urlpatterns = [
    path('register/', register, name='register'),
    path('login/', login, name='login'),
    path('logout/', logout, name='logout'),
    path('check-email/', check_email, name='check_email'),
    path('confirm_email/<int:user_id>/<str:token>/', confirm_email, name='confirm_email'),
    path('profile/', profile, name='profile'),
]