import logging

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import AnonymousUser
from django.contrib import messages

from chat.forms import LoginForm
from chat.db_selectors import user_username_taken
from chat.db_services import user_create


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
            username = credentials['username']
            password = credentials['password']

            user = authenticate(request, **credentials)
            username_taken = user_username_taken(username=username)

            if user is not None:
                login(request, user)
                return redirect('chat:index')
            elif user is None and not username_taken:
                user = user_create(username=username, password=password)
                login(request, user)
                return redirect('chat:index')
            else:
                msg = 'Username taken or wrong password'
                messages.warning(request, message=msg)

    context = {'form': LoginForm}
    return render(request, 'registration/login.html', context)
