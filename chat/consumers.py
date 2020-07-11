#!/usr/bin/env python3
# -*-encoding: utf-8-*-
# Author: Danil Kovalenko

import json
import typing as tp
from channels.generic.websocket import AsyncWebsocketConsumer

from chat.managers import AbstractManager, ReceiveManager, InitManager, \
    UserTrackManager


class ChatConsumerBase(AsyncWebsocketConsumer):
    """
    Chat consumer base class

    Implements routines required to support managers protocol.
    Managers protocol here -- a way of factoring out highly detailed code.
    As application logic may grow infinitely it seems as a bad idea to keep it
    in consumer class.
    Instead we apply next approach: all detailed logic in separate class --
    `Manager`. Manager implements `__init__` `on_connect` and `on_disconnect`
    Then subclass of `ChatConsumerBase` defines, which managers he wants ho
    employ by defining them in `managers_cls` class attribute.
    On each connect-disconnect all defined managers are notified via calling
    specific methods.
    """

    managers_cls: tp.Iterable[tp.Type[AbstractManager]] = []

    async def handle_auth(self):
        if not self.scope['user'].is_anonymous:
            await self.accept()
            return True
        await self.close()
        return False

    async def init_managers(self):
        self._managers = [m(self) for m in self.managers_cls]

    async def managers_notify_connect(self):
        for manager in self._managers:
            await manager.on_connect()

    async def managers_notify_disconnect(self):
        for manager in self._managers:
            await manager.on_disconnect()

    async def managers_notify_receive(self, text_data, bytes_data):
        for manager in self._managers:
            await manager.on_receive(text_data, bytes_data)

    async def connect(self):
        if not await self.handle_auth(): return
        await self.init_managers()
        await self.managers_notify_connect()

    async def receive(self, text_data=None, bytes_data=None):
        await self.managers_notify_receive(text_data, bytes_data)

    async def disconnect(self, code):
        await self.managers_notify_disconnect()
        self._managers.clear()


class ChatConsumer(ChatConsumerBase):

    room_name = 'chat'
    managers_cls = [InitManager, UserTrackManager, ReceiveManager]

    async def connect(self):
        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await super().connect()

        # add channel to group of channels for given user
        username = self.scope['user'].username
        await self.channel_layer.group_add(username, self.channel_name)

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.room_name,self.channel_name)
        await super().disconnect(code)

        # remove channel from group of channels for given user
        username = self.scope['user'].username
        await self.channel_layer.group_discard(username, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        await super().receive(text_data, bytes_data)

    async def chat_message(self, event):
        await self.send(json.dumps(event))

    async def chat_servicemessage(self, event):
        await self.send(json.dumps(event))

    async def online_connect(self, event):
        await self.send(json.dumps(event))

    async def online_disconnect(self, event):
        await self.send(json.dumps(event))

    async def user_mention(self, event):
        await self.send(json.dumps(event))
