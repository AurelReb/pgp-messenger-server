from django.contrib import admin
from message.models import Conversation, Message

admin.site.register(Conversation)
admin.site.register(Message)
