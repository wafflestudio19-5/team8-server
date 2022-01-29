from email import charset
from rest_framework import status, viewsets, permissions
from rest_framework.response import Response

from django.db.models import Q
from django.shortcuts import get_object_or_404

from article.models import Article
from chat.models import ChatRoom
from chat.serializers import ChatRoomSerializer


class ChatRoomViewSet(viewsets.GenericViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ChatRoomSerializer
    queryset = ChatRoom.objects.all()

    # make chatroom
    def post(self, request):
        user = request.user
        article_id = request.data.get("article_id")
        article = get_object_or_404(Article, pk=article_id)
        room_name = str(user.id) + "_" + str(article_id)

        # already exists then get chatroom
        if self.queryset.filter(name=room_name).exists():
            chatroom = self.queryset.get(name=room_name)
        else:
            chatroom = ChatRoom.objects.create(
                name=room_name, article=article, seller=article.seller, buyer=user
            )

        return Response(
            ChatRoomSerializer(chatroom, context={"user": user}).data,
            status=status.HTTP_201_CREATED,
        )

    # show all chatrooms of user
    def list(self, request):
        user = request.user
        chatrooms = self.queryset.filter(
            (Q(seller=user) & Q(valid_user__contains="s"))
            | (Q(buyer=user) & Q(valid_user__contains="b"))
        ).exclude(article__isnull=True)
        return Response(
            ChatRoomSerializer(chatrooms, many=True, context={"user": user}).data,
            status=status.HTTP_200_OK,
        )

    # show chatrooms which belongs to pk-th article
    def retrieve(self, request, pk=None):
        if pk is None:
            return Response("올바른 요청을 보내주세요.", status=status.HTTP_403_FORBIDDEN)

        if not Article.objects.filter(id=pk).exists():
            return Response("해당하는 상품이 존재하지 않습니다.", status=status.HTTP_404_NOT_FOUND)

        user = request.user
        article = Article.objects.get(id=pk)
        if article.seller != user:
            return Response("해당 유저의 상품이 아닙니다.", status=status.HTTP_403_FORBIDDEN)

        chatrooms = article.chatrooms.filter(valid_user__contains="s")
        return Response(
            ChatRoomSerializer(chatrooms, many=True, context={"user": user}).data,
            status=status.HTTP_200_OK,
        )

    # make chatrooms from user
    def destroy(self, request, pk=None):
        if pk is None:
            return Response("올바른 요청을 보내주세요.", status=status.HTTP_400_BAD_REQUEST)

        if not ChatRoom.objects.filter(name=pk).exists():
            return Response("해당하는 채팅방이 존재하지 않습니다.", status=status.HTTP_404_NOT_FOUND)

        user = request.user
        chatroom = ChatRoom.objects.get(name=pk)
        if user not in [chatroom.seller, chatroom.buyer]:
            return Response("해당 유저의 채팅방이 아닙니다.", status=status.HTTP_403_FORBIDDEN)

        if user == chatroom.seller:
            chatroom.valid_user = chatroom.valid_user.replace("s", " ")
        else:
            chatroom.valid_user = chatroom.valid_user.replace("b", " ")
        chatroom.save()
        return Response("채팅방을 나갔습니다.", status=status.HTTP_200_OK)
