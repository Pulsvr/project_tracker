from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    """Расширенная модель пользователя с аватаром и подтверждением email"""
    avatar = models.ImageField(null=True, blank=True, upload_to='avatars/')
    email_confirmed = models.BooleanField(default=False, verbose_name="Почта подтверждена")

    @property
    def get_avatar(self):
        """Возвращает URL аватара или генерирует аватар по имени пользователя"""
        if self.avatar:
            return self.avatar.url
        return f'https://ui-avatars.com/api/?background=random&name={self.username}'
