#!/usr/bin/env python3
# -*-encoding: utf-8-*-
# Author: Danil Kovalenko

from django.contrib import admin
from django.urls import path

import chat.views

app_name = 'chat'
urlpatterns = [
    path('register/', chat.views.register, name='register'),
    path('', chat.views.index, name='index')
]
