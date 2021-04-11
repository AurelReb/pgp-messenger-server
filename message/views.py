from rest_framework.viewsets import ModelViewSet

from message.mixins import ReadWriteSerializerMixin
from message.models import Conversation
from message.serializers import (
    ConversationReadSerializer, ConversationWriteSerializer)


class ConversationViewSet(ReadWriteSerializerMixin, ModelViewSet):
    read_serializer_class = ConversationReadSerializer
    write_serializer_class = ConversationWriteSerializer

    def get_queryset(self):
        return Conversation.objects.filter(users=self.request.user)
