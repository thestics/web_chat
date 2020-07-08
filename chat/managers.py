#!/usr/bin/env python3
# -*-encoding: utf-8-*-
# Author: Danil Kovalenko

import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async as db

from chat.db_selectors import active_user_get, chat_message_all, active_user_online_users
from chat.db_services import active_user_connections_decr, active_user_connections_incr


class UserTrackManager:
    """User track manager, tracks online users"""

    room_name = 'chat'

    def __init__(self, consumer: AsyncWebsocketConsumer):
        self.scope = consumer.scope
        self.send = consumer.send
        self.group_send = consumer.channel_layer.group_send

    async def handle_connect(self):
        active_record = await self.get_user_active_record()

        if active_record.active_connections == 0:
            event_data = {
                'type': 'online.connect',
                'user': self.scope['user'].username
            }
            # notify all
            await self.group_send(self.room_name, event_data)
            await self.send(json.dumps(event_data))

        await db(active_user_connections_incr)(active_user=active_record)

    async def handle_disconnect(self, code):
        active_record = await self.get_user_active_record()
        await db(active_user_connections_decr)(active_user=active_record)

        if active_record.active_connections == 0:
            event_data = {
                'type': 'online.disconnect',
                'user': self.scope['user'].username
            }
            # notify all
            await self.group_send(self.room_name, event_data)
            await self.send(json.dumps(event_data))

    async def get_user_active_record(self):
        """Get record about number of active connections for given user"""
        return await db(active_user_get)(user=self.scope['user'])


class InitManager:
    """
    Initialization manager.

    Sends init message about chat history and current online
    """

    def __init__(self, consumer: AsyncWebsocketConsumer):
        self.send = consumer.send

    async def init(self):
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
