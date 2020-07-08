from django.db import models
from django.contrib.auth.models import User

from chat.utils import datetime_to_dict


class ChatMessage(models.Model):

    text = models.CharField(max_length=8192)
    sent = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    def as_dict(self):
        user_name = self.author.username
        dict_date = datetime_to_dict(self.sent)
        return {'message': self.text, 'sent': dict_date, 'author': user_name}

    def __str__(self):
        if len(self.text) > 16:
            text = self.text[:16] + '...'
        else:
            text = self.text
        author = self.author.username
        sent = str(self.sent)
        return f"ChatMessage({text}, {author}, {sent})"

    def __repr__(self):
        return str(self)


class ActiveUser(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    active_connections = models.IntegerField(default=0)

    def as_dict(self):
        username = self.user.username
        return {'user': username, 'connections': self.active_connections}
