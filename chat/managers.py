#!/usr/bin/env python3
# -*-encoding: utf-8-*-
# Author: Danil Kovalenko

import abc
import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async as db

from chat.db_selectors import active_user_get, chat_message_all, active_user_online_users
from chat.db_services import active_user_connections_decr, active_user_connections_incr, chat_message_create
from chat.utils import datetime_to_json
from chat.const import CHAT_ROOM_NAME


class ManagerError(Exception): pass


class MessageSchemaError(ManagerError): pass


class AbstractManager(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def __init__(self, consumer: AsyncWebsocketConsumer):
        pass

    @abc.abstractmethod
    async def on_connect(self):
        pass

    @abc.abstractmethod
    async def on_disconnect(self):
        pass

    @abc.abstractmethod
    async def on_receive(self, text_data=None, bytes_data=None):
        pass


class UserTrackManager(AbstractManager):
    """User track manager, tracks online users"""

    def __init__(self, consumer: AsyncWebsocketConsumer):
        super().__init__(consumer)
        self.scope = consumer.scope
        self.send = consumer.send
        self.group_send = consumer.channel_layer.group_send

    async def on_connect(self):
        active_record = await self.get_user_active_record()

        if active_record.active_connections == 0:
            event_data = {
                'type': 'online.connect',
                'user': self.scope['user'].username
            }
            # notify all
            await self.group_send(CHAT_ROOM_NAME, event_data)
            await self.send(json.dumps(event_data))
            await self.send_service_msg_connect()

        await db(active_user_connections_incr)(active_user=active_record)

    async def on_disconnect(self):
        active_record = await self.get_user_active_record()
        await db(active_user_connections_decr)(active_user=active_record)

        if active_record.active_connections == 0:
            event_data = {
                'type': 'online.disconnect',
                'user': self.scope['user'].username
            }
            # notify all
            await self.group_send(CHAT_ROOM_NAME, event_data)
            await self.send(json.dumps(event_data))
            await self.send_service_msg_disconnect()

    async def on_receive(self, text_data=None, bytes_data=None): pass

    async def get_user_active_record(self):
        """Get record about number of active connections for given user"""
        return await db(active_user_get)(user=self.scope['user'])

    async def send_service_msg_connect(self):
        username = self.scope['user'].username
        message = f'User {username} joined'
        await db(chat_message_create)(text=message, author=None, service_msg=True)
        await self.group_send(CHAT_ROOM_NAME,
                              {'type': 'chat.servicemessage',
                               'message': message})

    async def send_service_msg_disconnect(self):
        username = self.scope['user'].username
        message = f'User {username} left'
        await db(chat_message_create)(text=message, author=None, service_msg=True)
        await self.group_send(CHAT_ROOM_NAME,
                              {'type': 'chat.servicemessage',
                               'message': message})

class InitManager(AbstractManager):
    """
    Initialization manager.

    Sends init message about chat history and current online
    """

    def __init__(self, consumer: AsyncWebsocketConsumer):
        super().__init__(consumer)
        self.consumer = consumer
        self.send = consumer.send

    async def on_connect(self):
        await self.send_whoami()
        await self.send_chat_history()
        await self.send_current_online()

    async def on_disconnect(self):
        pass

    async def on_receive(self, text_data=None, bytes_data=None): pass

    async def get_chat_messages(self):
            history = await db(chat_message_all)()
            return history

    async def get_online_users(self):
        users = await db(active_user_online_users)()
        return users

    async def send_whoami(self):
        username = self.consumer.scope['user'].username,

        # username is a tuple here
        response = {'type': 'init.whoami', 'user': username[0]}
        await self.send(json.dumps(response))

    async def send_chat_history(self):
        msg_history = await self.get_chat_messages()
        data = [await db(m.as_dict)() for m in msg_history]

        event_data = {
            'type': 'init.chat_history',
            'data': data
        }
        await self.send(text_data=json.dumps(event_data))

    async def send_current_online(self):
        online_users = await self.get_online_users()
        event_data = {
            'type': 'init.online_users',
            'data': [await db(u.as_dict)() for u in online_users]
        }
        await self.send(text_data=json.dumps(event_data))


class ReceiveManager(AbstractManager):
    """

    Handles socket.receive events and dispatches them to corresponding handlers
    """

    def __init__(self, consumer: AsyncWebsocketConsumer):
        super().__init__(consumer)
        self.consumer = consumer

    async def on_connect(self):
        pass

    async def on_disconnect(self):
        pass

    async def dispatch_receive_event(self, event):
        """Derive method name and dispatch event to it"""
        if 'type' not in event:
            raise MessageSchemaError(f'Expected `type` field in event. Got: {event}')
        handler_name = event['type'].lower().replace('.', '_')
        handler = getattr(self, handler_name)
        await handler(event)

    async def on_receive(self, text_data=None, bytes_data=None):
        event = json.loads(text_data)
        await self.dispatch_receive_event(event)

    # dispatchable handlers

    async def user_mention(self, event):
        """Identify user channel by user name, send toast"""
        event['by'] = self.consumer.scope['user'].username
        target_username = event['name']

        await self.consumer.channel_layer.group_send(target_username, event)

    async def chat_servicemessage(self, event):
        """Handle chat service messages (joined channel, left channel)"""
        await self.consumer.channel_layer.group_send(CHAT_ROOM_NAME, event)

    async def chat_message(self, event):
        """Handle chat message"""
        user = self.consumer.scope['user']
        message = event['message']
        msg = await db(chat_message_create)(text=message, author=user)

        to_send = {'type': 'chat.message',
                   'message': message,
                   'author': user.username,
                   'sent': datetime_to_json(msg.sent)}

        await self.consumer.channel_layer.group_send(CHAT_ROOM_NAME, to_send)
