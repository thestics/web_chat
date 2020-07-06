#!/usr/bin/env python3
# -*-encoding: utf-8-*-
# Author: Danil Kovalenko

from django.forms import Form, CharField, PasswordInput


class LoginForm(Form):
    username = CharField(label='username', max_length=128)
    password = CharField(label='password', max_length=128, widget=PasswordInput())
