from django.urls import path
from django.urls.conf import include
from rest_framework_nested import routers

from message.views import (
    ConversationViewSet,
    MessageNestedViewSet,
    MessageViewSet,
)

router = routers.DefaultRouter()
router.register('conversations', ConversationViewSet, 'conversations')
router.register('messages', MessageViewSet, 'messages')

conversations_router = routers.NestedSimpleRouter(
    router, 'conversations', lookup='conversation')
conversations_router.register(
    'messages', MessageNestedViewSet, basename='conversation-messages')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(conversations_router.urls)),
]
