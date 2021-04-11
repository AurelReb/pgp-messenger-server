from django.db import models
from core.models import User


class Conversation(models.Model):
    users = models.ManyToManyField(User, related_name="conversations")
    name = models.CharField(max_length=64, blank=True)

    def __str__(self) -> str:
        return self.name


class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False)
    conversation = models.ForeignKey(Conversation,
                                     on_delete=models.CASCADE,
                                     null=False,
                                     related_name="messages")
    message = models.TextField(null=False, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
