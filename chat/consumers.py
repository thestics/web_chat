#!/usr/bin/env python3
# -*-encoding: utf-8-*-
# Author: Danil Kovalenko

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from chat.models import ChatMessage


class ChatConsumer(AsyncWebsocketConsumer):

    room_name = 'chat'

    async def connect(self):
        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.room_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        user = self.scope['user']
        message = text_data_json['message']
        await database_sync_to_async(ChatMessage.objects.create)(text=message, author=user)

        to_send = {'type': 'chat_message',
                   'message': message}
        await self.channel_layer.group_send(self.room_name, to_send)

    async def chat_message(self, event):
        msg = event['message']
        await self.send(text_data=json.dumps({'message': msg}))
