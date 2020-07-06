#!/usr/bin/env python3
# -*-encoding: utf-8-*-
# Author: Danil Kovalenko

import json


def datetime_to_dict(d):
    attr_names = ('year', 'month', 'day', 'hour', 'minute',
                  'second', 'microsecond', 'tzinfo')
    res = {}
    for name in attr_names:
        val = getattr(d, name)
        res[name] = str(val)
    return res


def datetime_to_json(d):
    val = datetime_to_dict(d)
    return json.dumps(val)
