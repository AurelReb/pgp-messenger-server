import json
from urllib.parse import parse_qsl
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.core.cache import cache

from core.models import User
from message.models import Conversation, Message
from message.serializers import MessageSerializer


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def authorize(self, ticket_uuid, conversation_id):
        try:
            self.conversation_id = conversation_id

            self.scope['has_ticket'] = bool(cache.get(ticket_uuid))
            self.scope['user'] = await sync_to_async(
                User.objects.get
            )(id=cache.get(ticket_uuid))
            self.scope['conversation'] = await sync_to_async(
                Conversation.objects.get
            )(id=self.conversation_id, users=self.scope['user'])

            # Destroy ticket for performance and security purposes
            if not cache.delete(ticket_uuid):
                raise Exception('Ticket not found')

        except (User.DoesNotExist, Conversation.DoesNotExist):
            raise Exception('Unauthorized')

    async def websocket_connect(self, event):
        try:
            query_string = self.scope['query_string'].decode('utf-8')
            query_params = dict(parse_qsl(query_string))
            # Check whether the websocket connection is authorized
            await self.authorize(
                query_params.get('ticket_uuid'),
                self.scope['url_route']['kwargs']['room_name']
            )

        except Exception:
            await self.close()
            return

        await self.connect()

    async def connect(self):
        self.room_group_name = 'chat_%s' % self.conversation_id

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
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
        text_data_json = json.loads(text_data)
        conversation = self.scope['conversation']
        data = await self.new_message(
            text_data_json['message'],
            self.scope['user'],
            conversation
        )

        # Send last message id so client can check whether it's synced
        prev_id = None
        last_msg = await sync_to_async(
            lambda c: Message.objects.filter(conversation=c).last()
        )(conversation)
        if last_msg:
            prev_id = last_msg.id

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'prev_id': prev_id,
                **data
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps(event))
