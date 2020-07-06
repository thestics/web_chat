#!/usr/bin/env python3
# -*-encoding: utf-8-*-
# Author: Danil Kovalenko

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from chat.models import ChatMessage, ActiveUser
from chat.utils import datetime_to_json


class UserTrackerProxy(AsyncWebsocketConsumer):

    async def connect(self):
        await super().connect()

        # avoid extra db calls
        if not await self.is_user_connected():
            await database_sync_to_async(ActiveUser.objects.create)(user=self.scope['user'])

    async def disconnect(self, code):
        await super().disconnect(code)

        # avoid extra db calls
        if await self.is_user_connected():
            target = ActiveUser.objects.filter
            active_user = await database_sync_to_async(target)(user=self.scope['user'])
            await database_sync_to_async(active_user.delete)()

    async def is_user_connected(self):
        user = self.scope['user']
        r = await database_sync_to_async(ActiveUser.objects.filter)(user=user)
        return await database_sync_to_async(r.exists)()


class ChatConsumer(UserTrackerProxy):

    room_name = 'chat'

    async def connect(self):
        await super().connect()
        await self.channel_layer.group_add(self.room_name, self.channel_name)

    async def disconnect(self, code):
        await super().disconnect(code)
        await self.channel_layer.group_discard(self.room_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        user = self.scope['user']
        message = text_data_json['message']
        msg = await database_sync_to_async(ChatMessage.objects.create)(text=message, author=user)

        to_send = {'type': 'chat_message',
                   'message': message,
                   'sent': datetime_to_json(msg.sent)}
        await self.channel_layer.group_send(self.room_name, to_send)

    async def chat_message(self, event):
        msg = event['message']
        user = self.scope['user']
        sent = event['sent']

        await self.send(text_data=json.dumps({'message': msg,
                                              'author': user.username,
                                              'sent': sent}))

    async def user_connected(self, event):
        ...

    async def user_disconnected(self, event):
        ...