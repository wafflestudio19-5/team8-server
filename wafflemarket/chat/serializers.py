from rest_framework import serializers

from user.serializers import UserSerializer
from location.serializers import LocationSerializer
from article.serializers import ArticleSerializer
from chat.models import Chat, ChatRoom


class ChatSerializer(serializers.ModelSerializer):
    is_sender = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Chat
        fields = (
            "id",
            "content",
            "is_sender",
        )

    def get_is_sender(self, chat):
        user = self.context["user"]
        return chat.sender == user


# give info to list chatrooms
class ChatRoomSerializer(serializers.ModelSerializer):

    roomname = serializers.SerializerMethodField(read_only=True)
    username = serializers.SerializerMethodField(read_only=True)
    location = serializers.SerializerMethodField(read_only=True)
    profile_image = serializers.SerializerMethodField(read_only=True)
    article_id = serializers.SerializerMethodField(read_only=True)
    product_image = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ChatRoom
        fields = (
            "roomname",
            "username",
            "location",
            "profile_image",
            "article_id",
            "product_image",
        )

    def get_roomname(self, chatroom):
        return chatroom.name

    def get_username(self, chatroom):
        user = self.context["user"]
        if chatroom.seller == user:
            return chatroom.buyer.username
        else:
            return chatroom.seller.username

    def get_location(self, chatroom):
        return LocationSerializer(chatroom.article.location).data

    def get_profile_image(self, chatroom):
        user = self.context["user"]
        if chatroom.seller == user:
            user = chatroom.buyer
        else:
            user = chatroom.seller
        return UserSerializer(user).data.get("profile_image")

    def get_article_id(self, chatroom):
        return chatroom.article.id

    def get_product_image(self, chatroom):
        return ArticleSerializer(chatroom.article, context=self.context).data.get(
            "product_images"
        )[0]
