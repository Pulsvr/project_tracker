from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import ForeignKey

from searches.models import Search


class CustomUser(AbstractUser):
    avatar = models.ImageField(null=True, blank=True, upload_to='avatars/')

    @property
    def get_avatar(self):
        if self.avatar:
            return self.avatar.url
        return f'https://ui-avatars.com/api/?background=random&name={self.username}'
