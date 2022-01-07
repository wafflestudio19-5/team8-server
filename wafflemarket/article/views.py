from rest_framework import status, viewsets, permissions
from rest_framework.serializers import Serializer
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.paginator import Paginator
from .serializers import ArticleCreateSerializer, ArticlePaginationValidator, ArticleSerializer
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
        user = request.user
        page_id = request.GET.get('page', None)
        category = request.GET.get('category', None)
        keyword = request.GET.get('keyword', None)
        category_list = ['디지털기기', '가구/인테리어', '생활/가공식품', '스포츠/레저', '여성의류', '게임/취미', '반려동물용품', '식물',
                    '삽니다', '생활가전', '유아동', '유아도서', '여성잡화', '남성패션/잡화', '뷰티/미용', '도서/티켓/음반', '기타 중고물품']
        user_category_list = []
        
        if keyword is None:
            # check categories to filter article
            if category is None:
                for i, enable in enumerate(list(user.interest)):
                    if enable == "1":
                        user_category_list.append(category_list[i])
            else:
                if category in category_list:
                    user_category_list.append(category)
                else:
                    return Response(data='올바른 카테고리를 지정해주세요.', status=status.HTTP_400_BAD_REQUEST)
            
            # filter article by category
            articles = self.queryset.filter(category__in=user_category_list)
        else:
            # filter article by keyword
            articles = self.queryset.filter(title__startswith=keyword)

        articles = articles.order_by('-created_at')
        pages = Paginator(articles, 15)

        # check if page_id is valid
        if page_id is None:
            return Response(self.get_serializer(articles, many=True).data, status=status.HTTP_200_OK)
        serializer = ArticlePaginationValidator(data={'page_id': page_id, 'article_num': articles.count()})
        serializer.is_valid(raise_exception=True)

        page_id = serializer.data.get('page_id')
        return Response(self.get_serializer(pages.page(page_id), many=True).data, status=status.HTTP_200_OK)
    
    def retrieve(self, request, pk=None):
        if Article.objects.filter(id=pk).exists():
            article = Article.objects.get(id=pk)
        else:
            return Response({"해당하는 게시글을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        return Response(self.get_serializer(article).data, status=status.HTTP_200_OK)
    
    
