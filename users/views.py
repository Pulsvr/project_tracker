from django.contrib.auth import authenticate, login as user_login, logout as user_logout, update_session_auth_hash
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect, get_object_or_404

from users.models import CustomUser
from users.utils import email_confirmation_token

def home(request):
    # Главная страница - редирект на поиски или вход
    if request.user.is_authenticated:
        return redirect('search')
    return redirect('login')

def register(request):
    # Регистрация нового пользователя с отправкой письма подтверждения
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']

        if username and email and password:
            # Проверяем валидность email
            try:
                validate_email(email)
            except ValidationError:
                error = "Введите корректный email адрес"
                return render(request, "users/sign_up.html", {"error": error})
            
            # Проверяем только username, email может быть неуникальным
            if CustomUser.objects.filter(username=username).exists():
                error = "Пользователь с таким именем уже существует"
            else:
                # Создаем пользователя с неактивным статусом
                try:
                    user = CustomUser.objects.create_user(
                        username=username,
                        email=email,
                        password=password,
                        is_active=False,
                    )

                    token = email_confirmation_token.make_token(user)
                    domain = get_current_site(request).domain

                    confirm_url = f"http://{domain}/confirm_email/{user.pk}/{token}"

                    send_mail(
                        subject="Подтверждение регистрации",
                        message=f"Перейдите по ссылке для подтверждения: {confirm_url}",
                        from_email="smolyak.off@yandex.ru",
                        recipient_list=[user.email],
                        fail_silently=False,
                    )

                    return redirect('check_email')
                except Exception as e:
                    # Обработка неожиданных ошибок при создании пользователя
                    error = f"Ошибка при регистрации: {str(e)}"
        else:
            error = "Заполните все поля"

        return render(request, "users/sign_up.html", {"error": error})

    return render(request, "users/sign_up.html")

def login(request):
    # Вход пользователя в систему
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        if username and password:
            user = authenticate(request, username=username, password=password)

            if user:
                user_login(request, user)
                return redirect('search')
            else:
                error = "Неверный логин или пароль"
        else:
            error = "Заполните поля"

        return render(request, 'users/sign_in.html', {"error": error})

    return render(request, 'users/sign_in.html')

def logout(request):
    # Выход пользователя из системы
    user_logout(request)
    return redirect('login')

def check_email(request):
    # Страница ожидания подтверждения email
    return render(request, "users/check_email.html")

def confirm_email(request, user_id, token):
    # Подтверждение email пользователя по токену
    user = get_object_or_404(CustomUser, pk=user_id)

    if email_confirmation_token.check_token(user, token):
        user.email_confirmed = True
        user.is_active = True
        user.save()
        return render(request, "users/confirm_success.html")

    return render(request, "users/confirm_failed.html")

def profile(request):
    # Страница профиля пользователя со сменой пароля и редактированием данных
    user = request.user

    if request.method == 'POST':
        # Проверяем, это смена пароля или редактирование профиля
        if 'old_password' in request.POST:
            # Смена пароля
            old_password = request.POST['old_password']
            new_password = request.POST['new_password']
            new_password_confirm = request.POST['new_password_confirm']

            if not user.check_password(old_password):
                return render(request, "users/profile.html", {
                    "user": user,
                    "error": "Старый пароль неверный"
                })

            if new_password != new_password_confirm:
                return render(request, "users/profile.html", {
                    "user": user,
                    "error": "Новые пароли не совпадают"
                })

            user.set_password(new_password)
            user.save()

            update_session_auth_hash(request, user)

            return render(request, "users/profile.html", {
                "user": user,
                "success": "Пароль успешно изменен"
            })
        else:
            # Редактирование профиля (first_name, last_name)
            user.first_name = request.POST.get('first_name', '')
            user.last_name = request.POST.get('last_name', '')
            user.save()
            
            return render(request, "users/profile.html", {
                "user": user,
                "success": "Данные профиля обновлены"
            })

    return render(request, 'users/profile.html', {
        'user': user,
    })