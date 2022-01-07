from rest_framework import status, viewsets, permissions
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import ArticleCreateSerializer, ArticleSerializer, CommentCreateSerializer
from .models import Article, Comment
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
    
    @action(detail=True, methods=['POST'])
    def comment(self, request, pk):
        if Article.objects.filter(id=pk).exists():
            article = Article.objects.get(id=pk)
        else:
            return Response({"해당하는 게시글을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = CommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.create(serializer.validated_data, request.user, article)
        return Response(self.get_serializer(article).data, status=status.HTTP_201_CREATED)

class CommentView(APIView):
    permission_classes = (permissions.IsAuthenticated, )
    
    def delete(self, request, a_id, c_id):
        if Article.objects.filter(id=a_id).exists():
            article = Article.objects.get(id=a_id)
        else:
            return Response({"해당하는 게시글을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        if Comment.objects.filter(id=c_id, article=article).exists():
            comment = Comment.objects.get(id=c_id, article=article)
        else:
            return Response({"해당하는 댓글을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        if comment.commenter!=request.user:
            return Response({"작성자 외에는 댓글을 삭제할 수 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        
        comment.deleted_at = timezone.now()
        comment.save()
        return Response(ArticleSerializer(article).data, status=status.HTTP_200_OK)
    
    def post(self, request, a_id, c_id):
        if Article.objects.filter(id=a_id).exists():
            article = Article.objects.get(id=a_id)
        else:
            return Response({"해당하는 게시글을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        if Comment.objects.filter(id=c_id, article=article).exists():
            comment = Comment.objects.get(id=c_id, article=article)
        else:
            return Response({"해당하는 댓글을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = CommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.create(serializer.validated_data, request.user, article, comment)
        return Response(ArticleSerializer(article).data, status=status.HTTP_201_CREATED)
        

