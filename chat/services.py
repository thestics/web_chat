#!/usr/bin/env python3
# -*-encoding: utf-8-*-
# Author: Danil Kovalenko

import typing as tp

from django.contrib.auth.models import User

from chat.models import ActiveUser, ChatMessage


def user_create(*, username: str, password: str) -> User:
    user = User.objects.create_user(username, password)
    active_user_create(user=user)
    return user


def active_user_create(*, user: User) -> ActiveUser:
    return ActiveUser.objects.create(user=user)


def active_user_connections_incr(*, active_user: ActiveUser):
    active_user.active_connections += 1
    active_user.save()


def active_user_connections_decr(*, active_user: ActiveUser):
    active_user.active_connections -= 1
    active_user.save()


def chat_message_create(*, text: str, author: User) -> ChatMessage:
    return ChatMessage.objects.create(text=text, author=author)
