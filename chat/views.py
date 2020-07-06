import logging

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import AnonymousUser, User

from chat.forms import LoginForm


log = logging.getLogger(__name__)


def index(request):
    if isinstance(request.user, AnonymousUser):
        return redirect('chat:register')

    if 'logout' in request.GET:
        logout(request)
        return redirect('chat:register')

    return render(request, 'index.html')


def register(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)

        if form.is_valid():
            credentials = form.cleaned_data
            user = authenticate(request, **credentials)

            if user is not None:
                login(request, user)
                return redirect('chat:index')
            else:
                user = User.objects.create_user(**credentials)
                login(request, user)
                return redirect('chat:index')

    return render(request, 'registration/login.html', {'form': LoginForm})
