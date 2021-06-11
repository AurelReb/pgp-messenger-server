import json
import re
import traceback
from urllib.parse import parse_qsl
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.core.cache import cache

from core.models import User
from message.models import Conversation, Message
from message.serializers import MessageSerializer


class StreamConsumer(AsyncJsonWebsocketConsumer):
    available_streams = '|'.join([
        r'([0-9]+|all)@chat$',
        r'user$'
    ])

    async def authorize(self, ticket_uuid):
        try:
            self.scope['has_ticket'] = bool(cache.get(ticket_uuid))
            self.scope['user'] = await sync_to_async(
                User.objects.get
            )(id=cache.get(ticket_uuid))

            await self.channel_layer.group_add(
                'user_%s' % self.scope['user'].id,
                self.channel_name
            )
            # Destroy ticket for performance and security purposes
            if not cache.delete(ticket_uuid):
                raise Exception('Ticket not found')

        except User.DoesNotExist:
            raise Exception('Unauthorized')

    async def websocket_connect(self, event):
        try:
            # Check whether the websocket connection is authorized
            await self.authorize(
                self.scope['url_route']['kwargs']['ticket_uuid'],
            )

        except Exception:
            traceback.print_exc()
            await self.close()
            return

        await self.connect()

    async def connect(self):
        self.room_group_names = []
        self.conversations = []
        self.all_chats = False
        self.user_stream = False
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room groups
        for room_group_name in self.room_group_names:
            await self.channel_layer.group_discard(
                self.convert_stream_to_group_name(room_group_name),
                self.channel_name
            )
        await self.channel_layer.group_discard(
            'user_%s' % self.scope['user'].id,
            self.channel_name
        )

    async def get_valid_conversations(self, streams):
        conversation_ids = []
        if 'all@chat' in streams:
            return await sync_to_async(
                lambda: list(
                    Conversation.objects.filter(
                        users=self.scope['user']
                    ).values_list('id', flat=True)
                )
            )()

        for stream in streams:
            splitted = stream.split('@')
            if 'chat' in stream and splitted[0].isnumeric():
                conversation_ids.append(splitted[0])

        return await sync_to_async(
            lambda: list(
                Conversation.objects.filter(
                    id__in=conversation_ids,
                    users=self.scope['user']
                ).values_list('id', flat=True)
            )
        )()

    def convert_stream_to_group_name(self, stream):
        # Replace @ with ascii-friendly char
        group_name = stream.replace('@', '_')
        return group_name

    async def subscribe(self, streams):
        new_streams_json = list(filter(
            lambda s: re.match(self.available_streams, s),
            list(dict.fromkeys(streams))
        ))
        if 'all@chat' in new_streams_json:
            self.all_chats = True
        if 'user' in new_streams_json:
            self.user_stream = True
        conversation_ids = await self.get_valid_conversations(new_streams_json)
        self.conversations = list(dict.fromkeys(
            self.conversations + conversation_ids))

        new_filtered_streams = list(filter(lambda s: ('chat' not in s),
                                           new_streams_json))
        new_filtered_streams += list(map(lambda c: '%s@chat' % c,
                                         conversation_ids))

        # Join room group for all streams
        for room_group_name in new_filtered_streams:
            if room_group_name != 'user':
                await self.channel_layer.group_add(
                    self.convert_stream_to_group_name(room_group_name),
                    self.channel_name
                )
        self.room_group_names = list(dict.fromkeys(
            self.room_group_names + new_filtered_streams))
        await self.list_subscriptions()

    async def unsubscribe(self, streams):
        streams_json = list(dict.fromkeys(streams))
        if 'all@chat' in streams_json:
            self.all_chats = False
            streams_json += list(filter(
                lambda s: ('chat' in s), self.room_group_names
            ))
        if 'user' in streams_json:
            self.user_stream = False
        self.room_group_names = list(filter(
            lambda s: s not in streams_json, self.room_group_names
        ))

        # Leave room groups
        for room_group_name in streams_json:
            await self.channel_layer.group_discard(
                self.convert_stream_to_group_name(room_group_name),
                self.channel_name
            )
        self.conversations = await self.get_valid_conversations(
            self.room_group_names)
        await self.list_subscriptions()

    async def list_subscriptions(self):
        data = {
            'type': 'websocket.list_subscriptions',
            'streams': self.room_group_names,
            'all@chat': self.all_chats
        }
        await self.send(text_data=json.dumps(data))

    # Get last message id so client can check whether it's synced
    async def get_last_message_id(self, conversation):
        last_msg = await sync_to_async(
            lambda c: Message.objects.filter(conversation=c).last()
        )(conversation)
        if last_msg:
            return last_msg.id

        return None

    async def new_message(self, message, conversation_id):
        conversation = await sync_to_async(
            lambda: Conversation.objects.filter(id__in=self.conversations)
            .get(id=conversation_id)
        )()

        serializer = MessageSerializer(data={
            'message': message
        })
        serializer.context['websocket'] = True
        serializer.context['user'] = self.scope['user']
        serializer.context['conversation'] = conversation

        serializer.is_valid(raise_exception=True)
        await sync_to_async(serializer.save)()

        prev_id = await self.get_last_message_id(conversation)
        room_group_name = '%s@chat' % conversation_id
        # Send message to room group
        await self.channel_layer.group_send(
            self.convert_stream_to_group_name(room_group_name),
            {
                'type': 'chat.new_message',
                'prev_id': prev_id,
                **serializer.data
            }
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            method = text_data_json.get('method')
            if method == 'websocket.subscribe':
                await self.subscribe(text_data_json['streams'])
            elif method == 'websocket.unsubscribe':
                await self.unsubscribe(text_data_json['streams'])
            elif method == 'websocket.list_subscriptions':
                await self.list_subscriptions()
            elif method == 'chat.new_message':
                await self.new_message(
                    text_data_json['message'],
                    text_data_json['conversation']
                )
            elif method is None:
                await self.send_error('No method sent in the request.')
            else:
                await self.send_error('Unknown method.')

        except Conversation.DoesNotExist:
            await self.send_error('Not subscribed to this conversation.')
        except KeyError:
            await self.send_error('Invalid request params.')
        except json.decoder.JSONDecodeError:
            await self.send_error('Invalid request format.')
        except Exception:
            traceback.print_exc()
            await self.send_error('Unknown error.')

    async def send_error(self, error):
        data = {'type': 'websocket.error', 'error': error}
        await self.send(text_data=json.dumps(data))

    # Receive event from room group
    async def send_ws_message_from_group_event(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps(event))

    async def user_new_conversation(self, event):
        stream = '%s@chat' % event['id']
        if self.all_chats:
            await self.subscribe([stream])
        if self.user_stream:
            await self.send_ws_message_from_group_event(event)

    async def user_delete_conversation(self, event):
        stream = '%s@chat' % event['id']
        if stream in self.room_group_names:
            await self.unsubscribe([stream])
        if self.user_stream:
            await self.send_ws_message_from_group_event(event)

    chat_new_message = send_ws_message_from_group_event
    chat_edit_message = send_ws_message_from_group_event
    chat_delete_message = send_ws_message_from_group_event
