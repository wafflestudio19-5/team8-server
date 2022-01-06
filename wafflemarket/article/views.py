from rest_framework import status, viewsets, permissions
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import ArticleCreateSerializer, ArticleSerializer
from .models import Article
from user.models import User
from django.utils import timezone

class ArticleViewSet(viewsets.GenericViewSet): 
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = ArticleSerializer
    queryset = Article.objects.all()
    
    def create(self, request):
        serializer = ArticleCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        article = serializer.create_article(serializer.validated_data, request.user)
        return Response(self.get_serializer(article).data, status=status.HTTP_201_CREATED)
    
    def update(self, request, pk=None):
        if Article.objects.filter(id=pk).exists():
            article = Article.objects.get(id=pk)
        else:
            return Response({"해당하는 게시글을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        if article.seller!=request.user:
            return Response({"작성자 외에는 게시글을 수정할 수 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ArticleCreateSerializer(article, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        article = serializer.update_article(serializer.validated_data, article)
        return Response(self.get_serializer(article).data, status=status.HTTP_200_OK)
    
    def destroy(self, request, pk=None):
        if Article.objects.filter(id=pk).exists():
            article = Article.objects.get(id=pk)
        else:
            return Response({"해당하는 게시글을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        if article.seller!=request.user:
            return Response({"작성자 외에는 게시글을 삭제할 수 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        
        article.delete()
        return Response({"success":True}, status=status.HTTP_200_OK)
    
    def list(self, request):
        article = Article.objects.all()
        return Response(self.get_serializer(article, many=True).data, status=status.HTTP_200_OK)
    
    def retrieve(self, request, pk=None):
        if Article.objects.filter(id=pk).exists():
            article = Article.objects.get(id=pk)
        else:
            return Response({"해당하는 게시글을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        return Response(self.get_serializer(article).data, status=status.HTTP_200_OK)
    
    
    
    @action(detail=True, methods=['PUT', 'DELETE'])
    def purchase(self, request, pk):
        if Article.objects.filter(id=pk).exists():
            article = Article.objects.get(id=pk)
        else:
            return Response({"해당하는 게시글을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        if article.seller!=request.user:
            return Response({"작성자 외에는 게시글의 상태를 변경할 수 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        
        if self.request.method == 'PUT':
            article.sold_at = timezone.now()
            article.save()
        elif self.request.method == 'DELETE':
            article.sold_at = None
            article.buyer = None
            article.save()
        return Response(self.get_serializer(article).data, status=status.HTTP_200_OK)
    
    
    @action(detail=True, methods=['PUT', 'DELETE'])
    def buyer(self, request, pk=None):
        if Article.objects.filter(id=pk).exists():
            article = Article.objects.get(id=pk)
        else:
            return Response({"해당하는 게시글을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        if article.seller!=request.user:
            return Response({"작성자 외에는 게시글의 상태를 변경할 수 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        if article.sold_at is None:
            return Response({"구매완료되지 않은 게시글에는 구매자가 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        
        if self.request.method == 'PUT':
            buyer_id = request.data.get('buyer_id')
            if User.objects.filter(id=buyer_id).exists():
                buyer = User.objects.get(id=buyer_id)
                if buyer==article.seller:
                    return Response({"게시글의 작성자는 구매할 수 없습니다."}, status=status.HTTP_403_FORBIDDEN)
                article.buyer = buyer
                article.save()
            else:
                return Response({"해당하는 구매자를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
            
        elif self.request.method == 'DELETE':
            article.buyer = None
            article.save()
            
        return Response(self.get_serializer(article).data, status=status.HTTP_200_OK)
    
