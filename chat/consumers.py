#!/usr/bin/env python3
# -*-encoding: utf-8-*-
# Author: Danil Kovalenko

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from chat.models import ChatMessage, ActiveUser
from chat.utils import datetime_to_json


class UserTrackerProxy(AsyncWebsocketConsumer):

    room_name = 'chat'

    async def connect(self):
        await self.accept()
        active_record = await self.get_user_active_record()
        if active_record.active_connections == 0:
            event_data = {
                'type': 'online.connect',
                'user': self.scope['user'].username
            }
            await self.channel_layer.group_send(self.room_name, event_data)
            await self.online_connect(event_data)
            # await self.channel_layer.send(self.channel_name, event_data)

        active_record.active_connections += 1
        await database_sync_to_async(active_record.save)()

    async def disconnect(self, code):
        active_record = await self.get_user_active_record()
        active_record.active_connections -= 1
        await database_sync_to_async(active_record.save)()

        if active_record.active_connections == 0:
            event_data = {
                'type': 'online.disconnect',
                'user': self.scope['user'].username
            }
            await self.channel_layer.group_send(self.room_name, event_data)
            await self.online_disconnect(event_data)
            # await self.channel_layer.send(self.channel_name, event_data)

    async def get_user_active_record(self):
        user = self.scope['user']
        target = ActiveUser.objects.get
        response = (await database_sync_to_async(target)(user=user))
        return response

    async def online_connect(self, event):
        await self.send(json.dumps(event))

    async def online_disconnect(self, event):
        await self.send(json.dumps(event))


class ChatConsumer(UserTrackerProxy):

    async def connect(self):
        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await super().connect()

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

        data = {'type': 'chat.message',
                'message': msg,
                'author': user.username,
                'sent': sent}
        await self.send(text_data=json.dumps(data))

    async def user_connected(self, event):
        ...

    async def user_disconnected(self, event):
        ...