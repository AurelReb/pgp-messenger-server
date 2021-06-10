from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<ticket_uuid>[0-9a-f-]+)/$', consumers.ChatConsumer.as_asgi()),
]