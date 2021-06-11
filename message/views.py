from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework import mixins
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from message.mixins import ReadWriteSerializerMixin
from message.models import Conversation, Message
from message.serializers import (
    ConversationReadSerializer, ConversationWriteSerializer, MessageSerializer)


class ConversationViewSet(ReadWriteSerializerMixin, ModelViewSet):
    read_serializer_class = ConversationReadSerializer
    write_serializer_class = ConversationWriteSerializer

    def get_queryset(self):
        return Conversation.objects.filter(users=self.request.user)

    # Send deleted message to websocket instances
    def destroy(self, request, *args, **kwargs):
        conv_id = self.get_object().id
        users = list(self.get_object().users.values_list('id', flat=True))
        ret = super().destroy(request, *args, **kwargs)
        channel_layer = get_channel_layer()
        for user_id in users:
            room_group = 'user_%s' % user_id
            async_to_sync(channel_layer.group_send)(
                room_group,
                {
                    'type': 'user.delete_conversation',
                    'id': conv_id,
                }
            )
        return ret


class MessageNestedViewSet(mixins.ListModelMixin,
                           mixins.CreateModelMixin,
                           GenericViewSet):
    serializer_class = MessageSerializer

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

    # Send deleted message to websocket instances
    def destroy(self, request, *args, **kwargs):
        msg_id = self.get_object().id
        conv_id = self.get_object().conversation.id
        ret = super().destroy(request, *args, **kwargs)
        channel_layer = get_channel_layer()
        chat_name = '%s_chat' % conv_id
        async_to_sync(channel_layer.group_send)(
            chat_name,
            {
                'type': 'chat.delete_message',
                'conversation': conv_id,
                'id': msg_id
            }
        )
        return ret
