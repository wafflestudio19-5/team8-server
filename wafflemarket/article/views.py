from rest_framework import status, viewsets, permissions
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import ArticleCreateSerializer, ArticleSerializer
from .models import Article, ProductImage

class ArticleViewSet(viewsets.GenericViewSet): 
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = ArticleSerializer
    queryset = Article.objects.all()
    
    def create(self, request):
        serializer = ArticleCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        image_count = int(serializer.data['image_count'])
        for i in range(1, image_count+1):
            field_name = 'product_image_'+str(i)
            if request.FILES.get(field_name) is None:
                return Response(data="업로드 형식이 올바르지 않습니다.", status=status.HTTP_400_BAD_REQUEST)

        article = serializer.create_article(serializer.validated_data, request.user)
        for i in range(1, image_count+1):
            field_name = 'product_image_'+str(i)
            product_image = request.FILES.get(field_name)
            ProductImage.objects.create(article=article, product_image=product_image)
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
    
    
