import logging

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import AnonymousUser, User
from django.contrib import messages

from chat.models import ActiveUser
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
            username_taken = User.objects.filter(username=credentials['username']).exists()

            if user is not None:
                login(request, user)
                return redirect('chat:index')
            elif user is None and not username_taken:
                user = User.objects.create_user(**credentials)
                ActiveUser.objects.create(user=user)
                login(request, user)
                return redirect('chat:index')
            else:
                msg = 'Username taken or wrong password'
                messages.warning(request, message=msg)

    context = {'form': LoginForm}
    return render(request, 'registration/login.html', context)
