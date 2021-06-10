import json
import traceback
from urllib.parse import parse_qsl
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.core.cache import cache

from core.models import User
from message.models import Conversation, Message
from message.serializers import MessageSerializer


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def authorize(self, ticket_uuid, conversations):
        try:
            self.scope['has_ticket'] = bool(cache.get(ticket_uuid))
            self.scope['user'] = await sync_to_async(
                User.objects.get
            )(id=cache.get(ticket_uuid))

            if conversations == 'all':
                self.conversations = await sync_to_async(
                    lambda **kwargs: list(Conversation.objects.filter(**kwargs)
                                          .values_list('id', flat=True))
                )(users=self.scope['user'])
            else:
                self.conversations = await sync_to_async(
                    lambda **kwargs: list(Conversation.objects.filter(**kwargs)
                                          .values_list('id', flat=True))
                )(id__in=json.loads(conversations), users=self.scope['user'])

            # Destroy ticket for performance and security purposes
            if not cache.delete(ticket_uuid):
                raise Exception('Ticket not found')
            if not len(self.conversations):
                raise Exception('Unauthorized')

        except (User.DoesNotExist, Conversation.DoesNotExist):
            raise Exception('Unauthorized')

    async def websocket_connect(self, event):
        try:
            query_string = self.scope['query_string'].decode('utf-8')
            query_params = dict(parse_qsl(query_string))
            # Check whether the websocket connection is authorized
            await self.authorize(
                self.scope['url_route']['kwargs']['ticket_uuid'],
                query_params.get('conversations'),
            )

        except Exception:
            traceback.print_exc()
            await self.close()
            return

        await self.connect()

    async def connect(self):
        self.room_group_names = ['chat_%s' % c for c in self.conversations]

        # Join room group for all chats
        for room_group_name in self.room_group_names:
            await self.channel_layer.group_add(
                room_group_name,
                self.channel_name
            )
        await self.accept()
        data = {
            'type': 'websocket.accept',
            'conversations': self.conversations
        }
        await self.send(text_data=json.dumps(data))

    async def disconnect(self, close_code):
        # Leave room groups
        for room_group_name in self.room_group_names:
            await self.channel_layer.group_discard(
                room_group_name,
                self.channel_name
            )

    async def new_message(self, message, user, conversation):
        serializer = MessageSerializer(data={
            'message': message
        })
        serializer.context['websocket'] = True
        serializer.context['user'] = user
        serializer.context['conversation'] = conversation

        serializer.is_valid(raise_exception=True)
        await sync_to_async(serializer.save)()

        return serializer.data

    # Receive message from WebSocket
    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            conversation = await sync_to_async(
                lambda: Conversation.objects.filter(id__in=self.conversations)
                .get(id=text_data_json['conversation'])
            )()

            # Get last message id so client can check whether it's synced
            prev_id = None
            last_msg = await sync_to_async(
                lambda c: Message.objects.filter(conversation=c).last()
            )(conversation)
            if last_msg:
                prev_id = last_msg.id

            data = await self.new_message(
                text_data_json['message'],
                self.scope['user'],
                conversation
            )

            room_group_name = 'chat_%s' % data['conversation']

            # Send message to room group
            await self.channel_layer.group_send(
                room_group_name,
                {
                    'type': 'chat.new_message',
                    'prev_id': prev_id,
                    **data
                }
            )

        except Conversation.DoesNotExist:
            await self.send_error('Not subscribed to this conversation.')
        except Exception:
            await self.send_error('Unknown error.')

    async def send_error(self, error):
        data = {'type': 'websocket.error', 'error': error}
        await self.send(text_data=json.dumps(data))

    # Receive event from room group
    async def send_ws_message_from_group_event(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps(event))

    chat_new_message = send_ws_message_from_group_event
    chat_edit_message = send_ws_message_from_group_event
    chat_delete_message = send_ws_message_from_group_event
