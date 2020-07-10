#!/usr/bin/env python3
# -*-encoding: utf-8-*-
# Author: Danil Kovalenko

import re

from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.forms import Form, CharField, PasswordInput, TextInput


def username_validator(value):
    regexp = r'[A-Za-z0-9.-]+'
    if re.fullmatch(regexp, value) is None:
        raise ValidationError(
            _("%(value)s must be a valid unicode string "
              "containing only ASCII alphanumerics, hyphens, or periods."),
            params={'value': value}
        )


class LoginForm(Form):
    username = CharField(label='Username',
                         max_length=128,
                         validators=[username_validator],
                         widget=TextInput(attrs={'class': 'form-control w-25'}))

    password = CharField(label='Password',
                         max_length=128,
                         widget=PasswordInput(attrs={'class': 'form-control w-25'}))
