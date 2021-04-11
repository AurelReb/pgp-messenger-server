from django.urls import path
from django.urls.conf import include
from rest_framework import routers
from message.views import ConversationViewSet

router = routers.DefaultRouter()
router.register('conversation', ConversationViewSet, 'conversation')

urlpatterns = [
    path('', include(router.urls)),
]
