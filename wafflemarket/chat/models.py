from django.db import models
from django.dispatch import receiver

from user.models import User
from article.models import Article


class ChatRoom(models.Model):
    name = models.CharField(max_length=100, unique=True)
    article = models.ForeignKey(
        Article, related_name="chatrooms", null=True, on_delete=models.SET_NULL
    )
    seller = models.ForeignKey(
        User, related_name="chatrooms_sold", null=True, on_delete=models.SET_NULL
    )
    buyer = models.ForeignKey(
        User, related_name="chatrooms_bought", null=True, on_delete=models.SET_NULL
    )


class Chat(models.Model):
    chatroom = models.ForeignKey(
        ChatRoom, related_name="chats", null=False, on_delete=models.CASCADE
    )
    sender = models.ForeignKey(
        User, related_name="chats", null=True, on_delete=models.SET_NULL
    )
    content = models.CharField(max_length=255, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
