from django.db import models
from django.contrib.auth.models import User


class ChatMessage(models.Model):

    text = models.CharField(max_length=8192)
    sent = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)

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
