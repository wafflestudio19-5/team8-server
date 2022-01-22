import json
from urllib.parse import parse_qs
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from chat.models import Chat
from chat.models import ChatRoom
from chat.serializers import ChatSerializer


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.roomname = self.scope['url_route']['kwargs']['roomname']
        self.room_group_name = 'chat_%s' % self.roomname
        self.chatroom = await self.get_chatroom(self.roomname)
        self.user = self.scope["user"]
        latest_message = parse_qs(self.scope["query_string"].decode()).get("latest_message")[0]

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        
        # send unread messages
        unread_messages = await self.get_unread_messages(latest_message)
        await self.send(text_data=json.dumps(
            await self.get_json_messages(unread_messages, many=True)
        ))

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        content = text_data_json['chat']
        chat = await self.create_chat(content)
        sender_id = await self.get_sender_id(chat)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'chat': await self.get_json_messages(chat),
                'sender_id': sender_id,
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        chat = event["chat"]
        chat["is_sender"] = await self.get_is_sender(event["sender_id"])

        # Send message to WebSocket
        await self.send(text_data=json.dumps(
            [chat]
        ))

    @database_sync_to_async
    def get_chatroom(self, roomname):
        if ChatRoom.objects.filter(name=self.roomname).exists():
            return ChatRoom.objects.get(name=self.roomname)
        else:
            return None

    @database_sync_to_async
    def get_unread_messages(self, latest_message=0):
        return self.chatroom.chats.filter(id__gt=latest_message).order_by("id")

    @database_sync_to_async
    def get_json_messages(self, messages, many=False):
        return ChatSerializer(messages, many=many, context={"user": self.user}).data

    @database_sync_to_async
    def create_chat(self, content):
        return Chat.objects.create(chatroom=self.chatroom, sender=self.user, content=content)

    @database_sync_to_async
    def get_sender_id(self, chat):
        return chat.sender.id

    @database_sync_to_async
    def get_is_sender(self, sender_id):
        return sender_id == self.user.id