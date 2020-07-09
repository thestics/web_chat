#!/usr/bin/env python3
# -*-encoding: utf-8-*-
# Author: Danil Kovalenko

import re

from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.forms import Form, CharField, PasswordInput


def username_validator(value):
    regexp = r'[A-Za-z0-9.-]+'
    if re.fullmatch(regexp, value) is None:
        raise ValidationError(
            _("%(value)s must be a valid unicode string "
              "containing only ASCII alphanumerics, hyphens, or periods."),
            params={'value': value}
        )


class LoginForm(Form):
    username = CharField(label='username', max_length=128, validators=[username_validator])
    password = CharField(label='password', max_length=128, widget=PasswordInput())
