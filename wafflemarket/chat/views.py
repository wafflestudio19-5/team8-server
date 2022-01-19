from rest_framework import status, viewsets, permissions
from rest_framework.response import Response

from article.models import Article
from chat.models import ChatRoom
from chat.serializers import ChatRoomSerializer


class ChatRoomViewSet(viewsets.GenericViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ChatRoomSerializer
    queryset = ChatRoom.objects.all()

    # show all chatrooms of user
    def list(self, request):
        user = request.user
        chatrooms = self.queryset.filter(seller=user)
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