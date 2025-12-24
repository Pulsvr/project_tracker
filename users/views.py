from django.contrib.auth import authenticate, login as user_login, logout as user_logout, update_session_auth_hash
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.shortcuts import render, redirect

from users.models import CustomUser
from users.utils import email_confirmation_token

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']

        if username and email and password:
            if not CustomUser.objects.filter(username=username, email=email).exists():
                user = CustomUser.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    is_active=False,
                )

                token = email_confirmation_token.make_token(user)
                domain = get_current_site(request).domain

                confirm_url = f"http://{domain}/users/confirm_email/{user.pk}/{token}"

                send_mail(
                    subject="Подтверждение регистрации",
                    message=f"Перейдите по ссылке для подтверждения: {confirm_url}",
                    from_email="z1tra@yandex.com",
                    recipient_list=['z1tra@yandex.ru'],
                    fail_silently=False,
                )

                return redirect('check_email')

            else:
                error = "Пользователь с таким именем или почтой уже существует"
        else:
            error = "Заполните все поля"

        return render(request, "users/sign_up.html", {"error": error})

    return render(request, "users/sign_up.html")

def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        if username and password:
            user = authenticate(request, username=username, password=password)

            if user:
                user_login(request, user)
                return redirect('projects_kanban')
            else:
                error = "Неверный логин или пароль"
        else:
            error = "Заполните поля"

        return render(request, 'users/sign_in.html', {"error": error})

    return render(request, 'users/sign_in.html')

def logout(request):
    user_logout(request)
    return redirect('login')

def check_email(request):
    return render(request, "users/check_email.html")

def confirm_email(request, user_id, token):
    user = CustomUser.objects.get(pk=user_id)

    if not user:
        return render(request, "users/confirm_failed.html")

    if email_confirmation_token.check_token(user, token):
        user.email_confirmed = True
        user.is_active = True
        user.save()
        return render(request, "users/confirm_success.html")

    return render(request, "users/confirm_failed.html")

def profile(request):
    user = request.user

    if request.method == 'POST':
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

    return render(request, 'users/profile.html', {
        'user': user,
    })