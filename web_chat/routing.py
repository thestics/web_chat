#!/usr/bin/env python3
# -*-encoding: utf-8-*-
# Author: Danil Kovalenko

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

from chat.routing import websocket_urlpatterns


application = ProtocolTypeRouter({

    'websocket': AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    )
})