from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/stream/(?P<ticket_uuid>[0-9a-f-]+)/$', consumers.StreamConsumer.as_asgi()),
]