import json
from channels.generic.websocket import AsyncWebsocketConsumer

from django.contrib.auth.models import AnonymousUser

from user.models import User
from chat.models import Chat
from chat.models import ChatRoom
from chat.serializers import ChatSerializer


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.roomname = self.scope['url_route']['kwargs']['roomname']
        self.room_group_name = 'chat_%s' % self.roomname
        self.chatroom = ChatRoom.objects.get(name=self.roomname)
        self.serializer = ChatSerializer
        user_id = self.scope["query_string"].get("user_id")
        latest_message = self.scope["query_string"].get("latest_message")
        try:
            self.user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            self.user = AnonymousUser()

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        
        # send unread messages
        if latest_message:
            unread_messages = self.chatroom.chats.filter(id__gt=latest_message).order_by("id")
            await self.send(text_data=json.dumps(
                self.serializer(unread_messages, many=True, context={"user": self.user}).data
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
        chat = Chat.objects.create(chatroom=self.chatroom, sender=self.user, content=content)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'chat': chat
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        chat = event['chat']

        # Send message to WebSocket
        await self.send(text_data=json.dumps(
            [self.serializer(chat, context={"user": self.user}).data]
        ))