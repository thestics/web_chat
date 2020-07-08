#!/usr/bin/env python3
# -*-encoding: utf-8-*-
# Author: Danil Kovalenko

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async as db

from chat.db_selectors import active_user_get, chat_message_all, active_user_online_users
from chat.db_services import active_user_connections_incr, active_user_connections_decr, chat_message_create
from chat.utils import datetime_to_json


class UserTrackerProxy(AsyncWebsocketConsumer):
    """Proxy consumer, tracks online users"""

    room_name = 'chat'

    async def connect(self):
        await self.accept()
        active_record = await self.get_user_active_record()

        if active_record.active_connections == 0:
            event_data = {
                'type': 'online.connect',
                'user': self.scope['user'].username
            }
            # notify all
            await self.channel_layer.group_send(self.room_name, event_data)

            # notify self
            await self.online_connect(event_data)

        await db(active_user_connections_incr)(active_user=active_record)

    async def disconnect(self, code):
        active_record = await self.get_user_active_record()
        await db(active_user_connections_decr)(active_user=active_record)

        if active_record.active_connections == 0:
            event_data = {
                'type': 'online.disconnect',
                'user': self.scope['user'].username
            }
            # notify all
            await self.channel_layer.group_send(self.room_name, event_data)

            # notify self
            await self.online_disconnect(event_data)

    async def get_user_active_record(self):
        """Get record about number of active connections for given user"""
        return await db(active_user_get)(user=self.scope['user'])

    async def online_connect(self, event):
        await self.send(json.dumps(event))

    async def online_disconnect(self, event):
        await self.send(json.dumps(event))


class InitProxy(UserTrackerProxy):
    """Proxy consumer. Handles init messages"""

    async def connect(self):
        await super().connect()
        await self.send_chat_history()
        await self.send_current_online()

    async def get_chat_messages(self):
        history = await db(chat_message_all)()
        return history

    async def get_online_users(self):
        users = await db(active_user_online_users)()
        return users

    async def send_chat_history(self):
        msg_history = await self.get_chat_messages()
        event_data = {
            'type': 'init.chat_history',
            'data': [await db(m.as_dict)() for m in msg_history]
        }
        await self.send(text_data=json.dumps(event_data))

    async def send_current_online(self):
        online_users = await self.get_online_users()
        event_data = {
            'type': 'init.online_users',
            'data': [await db(u.as_dict)() for u in online_users]
        }
        await self.send(text_data=json.dumps(event_data))


class ChatConsumer(InitProxy):

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
        msg = await db(chat_message_create)(text=message, author=user)

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
