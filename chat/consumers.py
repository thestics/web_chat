#!/usr/bin/env python3
# -*-encoding: utf-8-*-
# Author: Danil Kovalenko

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async as db

from chat.db_services import chat_message_create
from chat.utils import datetime_to_json
from chat.managers import InitManager, UserTrackManager


class ChatConsumer(AsyncWebsocketConsumer):
    room_name = 'chat'

    async def connect(self):
        self.user_track_manager = UserTrackManager(self)

        if not await self.handle_auth():
            return

        await InitManager(self).init()
        await self.user_track_manager.handle_connect()
        await self.channel_layer.group_add(self.room_name, self.channel_name)

        # add channel to group of channels for given user
        username = self.scope['user'].username
        await self.channel_layer.group_add(username, self.channel_name)

    async def disconnect(self, code):
        await super().disconnect(code)
        await self.channel_layer.group_discard(self.room_name,
                                               self.channel_name)

        # remove channel from group of channels for given user
        username = self.scope['user'].username
        await self.channel_layer.group_discard(username, self.channel_name)

        await self.user_track_manager.handle_disconnect(code)

    async def receive(self, text_data=None, bytes_data=None):
        print(text_data)
        text_data_json = json.loads(text_data)

        event_type = text_data_json.get('type', '')

        if event_type == 'user.mention':
            await self.handle_user_mention(text_data_json)
            return

        elif event_type == 'user.whoami':
            await self.who_am_i()
            return

        user = self.scope['user']
        message = text_data_json['message']
        msg = await db(chat_message_create)(text=message, author=user)

        to_send = {'type': 'chat.message',
                   'message': message,
                   'author': user.username,
                   'sent': datetime_to_json(msg.sent)}

        await self.channel_layer.group_send(self.room_name, to_send)

    async def handle_auth(self):
        if not self.scope['user'].is_anonymous:
            await self.accept()
            return True
        await self.close()
        return False

    async def chat_message(self, event):
        await self.send(json.dumps(event))

    async def online_connect(self, event):
        await self.send(json.dumps(event))

    async def online_disconnect(self, event):
        await self.send(json.dumps(event))

    async def handle_user_mention(self, event):
        """Identify user channel by user name, send toast"""
        event['by'] = self.scope['user'].username
        target_username = event['name']

        await self.channel_layer.group_send(target_username, event)

    async def who_am_i(self):
        await self.send(
            text_data=json.dumps({'type': 'user.whoami',
                                  'user': self.scope['user'].username})
        )

    async def user_mention(self, event):
        await self.send(text_data=json.dumps(event))
