#!/usr/bin/env python3
# -*-encoding: utf-8-*-
# Author: Danil Kovalenko

from django.urls import path

from chat.consumers import ChatConsumer


websocket_urlpatterns = [
    path('ws/chat', ChatConsumer)
]