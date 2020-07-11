#!/usr/bin/env python3
# -*-encoding: utf-8-*-
# Author: Danil Kovalenko

# Selectors from databases
#
# All business logic, dedicated to database read is implemented here

import typing as tp

from django.contrib.auth.models import User

from chat.models import ActiveUser, ChatMessage


def user_username_taken(*, username: str) -> bool:
    return User.objects.filter(username=username).exists()


def active_user_get(*, user: User) -> ActiveUser:
    active_user = ActiveUser.objects.get(user=user)
    return active_user


def active_user_online_users() -> tp.Iterable[ActiveUser]:
    return list(ActiveUser.objects.filter(active_connections__gt=0))


def chat_message_all() -> tp.Iterable[ChatMessage]:
    return list(ChatMessage.objects.order_by("sent"))