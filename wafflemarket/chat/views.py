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
        chatroom = ChatRoom.objects.create(name=room_name, article=article, seller=article.seller, buyer=user)
        return Response(self.get_serializer(chatroom).data, status=status.HTTP_201_CREATED)

    # show all chatrooms of user
    def list(self, request):
        user = request.user
        chatrooms = self.queryset.filter(Q(seller=user)|Q(buyer=user))
        return Response(self.get_serializer(chatrooms, many=True).data, status=status.HTTP_200_OK)

    # show chatrooms which belongs to pk-th article
    def retrieve(self, request, pk=None):
        if pk is not None:
            if Article.objects.filter(id=pk).exists():
                article = Article.objects.get(id=pk)
                if article.seller == request.user:
                    return Response(
                        self.get_serializer(article.chatrooms, many=True).data, status=status.HTTP_200_OK
                    )
                else:
                    return Response(
                        "해당 유저의 상품이 아닙니다.", status=status.HTTP_403_FORBIDDEN
                    )
            else:
                return Response(
                    "해당하는 상품이 존재하지 않습니다.", status=status.HTTP_404_NOT_FOUND
                )
        else:
            return Response("올바른 요청을 보내주세요.", status=status.HTTP_403_FORBIDDEN)