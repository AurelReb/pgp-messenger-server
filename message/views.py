from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework import mixins

from message.mixins import ReadWriteSerializerMixin
from message.models import Conversation, Message
from message.permissions import ConversationPermission
from message.serializers import (
    ConversationReadSerializer,
    ConversationWriteSerializer,
    MessageSerializer
)


class ConversationViewSet(ReadWriteSerializerMixin, ModelViewSet):
    read_serializer_class = ConversationReadSerializer
    write_serializer_class = ConversationWriteSerializer

    def get_queryset(self):
        return Conversation.objects.filter(users=self.request.user)


class MessageNestedViewSet(mixins.ListModelMixin,
                           mixins.CreateModelMixin,
                           GenericViewSet):
    serializer_class = MessageSerializer
    permission_classes = (ConversationPermission,)

    def get_queryset(self):
        return Message.objects.filter(
            conversation=self.kwargs['conversation_pk'])


class MessageViewSet(mixins.RetrieveModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.DestroyModelMixin,
                     mixins.ListModelMixin,
                     GenericViewSet):
    serializer_class = MessageSerializer

    def get_queryset(self):
        return Message.objects.filter(user=self.request.user)
