from datetime import datetime, timedelta

from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from django.core.files.base import ContentFile
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone

from user.models import User
from article.models import Article, ProductImage, Comment
from article.serializers import (
    ArticleCreateSerializer,
    ArticlePaginationValidator,
    ArticleSerializer,
    CommentCreateSerializer,
    CommentSerializer,
)
from review.models import Review


class ArticleViewSet(viewsets.GenericViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ArticleSerializer
    queryset = Article.objects.all()

    def create(self, request):
        serializer = ArticleCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        image_count = int(serializer.validated_data["image_count"])
        for i in range(1, image_count + 1):
            field_name = "image_" + str(i)
            if request.FILES.get(field_name) is None:
                return Response(
                    data="업로드 형식이 올바르지 않습니다.", status=status.HTTP_400_BAD_REQUEST
                )
                
        article = serializer.create_article(serializer.validated_data, request.user)
        for i in range(1, image_count + 1):
            field_name = "image_" + str(i)
            image = request.FILES.get(field_name)
            thumbnail = ContentFile(image.read())
            thumbnail.name = image.name
            ProductImage.objects.create(
                article=article, product_image=image, product_thumbnail=thumbnail
            )
        return Response(
            ArticleSerializer(
                article, 
                context={"user": request.user}
            ).data, 
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, pk=None):
        if Article.objects.filter(id=pk).exists():
            article = Article.objects.get(id=pk)
        else:
            return Response({"해당하는 게시글을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        if article.seller != request.user:
            return Response(
                {"작성자 외에는 게시글을 수정할 수 없습니다."}, status=status.HTTP_403_FORBIDDEN
            )

        serializer = ArticleCreateSerializer(article, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        image_count = int(serializer.validated_data["image_count"])
        for i in range(1, image_count + 1):
            field_name = "product_image_" + str(i)
            if request.FILES.get(field_name) is None:
                return Response(
                    data="업로드 형식이 올바르지 않습니다.", status=status.HTTP_400_BAD_REQUEST
                )
                
        article = serializer.create_article(serializer.validated_data, request.user)
        for i in range(1, image_count + 1):
            field_name = "image_" + str(i)
            image = request.FILES.get(field_name)
            thumbnail = ContentFile(image.read())
            thumbnail.name = image.name
            ProductImage.objects.create(
                article=article, product_image=image, product_thumbnail=thumbnail
            )
        article = serializer.update_article(serializer.validated_data, article)
        
        return Response(
            ArticleSerializer(
                article, context={"user": request.user},
            ).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["PUT", "DELETE"])
    def purchase(self, request, pk):
        if Article.objects.filter(id=pk).exists():
            article = Article.objects.get(id=pk)
        else:
            return Response({"해당하는 게시글을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        if article.seller != request.user:
            return Response(
                {"작성자 외에는 게시글의 상태를 변경할 수 없습니다."},
                status=status.HTTP_405_METHOD_NOT_ALLOWED,
            )

        if self.request.method == "PUT":
            article.sold_at = timezone.now()
            article.save()
            
        elif self.request.method == "DELETE":
            
            # delete reviews when canceling purchase
            if Review.objects.filter(review_type="seller", article=article).exists():
                seller_review = Review.objects.get(review_type="seller", article=article)
                seller_review.delete()
            if Review.objects.filter(review_type="buyer", article=article).exists():
                buyer_review = Review.objects.get(review_type="buyer", article=article)
                buyer_review.delete()
                
            article.sold_at = None
            article.buyer = None
            article.save()
            
        return Response(
            ArticleSerializer(
                article, context={"user": request.user},
            ).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["PUT", "DELETE"])
    def buyer(self, request, pk=None):
        if Article.objects.filter(id=pk).exists():
            article = Article.objects.get(id=pk)
        else:
            return Response({"해당하는 게시글을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        if article.seller != request.user:
            return Response(
                {"작성자 외에는 게시글의 상태를 변경할 수 없습니다."}, status=status.HTTP_403_FORBIDDEN
            )

        if self.request.method == "PUT":
            buyer_id = request.data.get("buyer_id")
            
            if not User.objects.filter(id=buyer_id).exists():
                return Response(
                    {"해당하는 구매자를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND
                )
                
            buyer = User.objects.get(id=buyer_id)
            
            # delete reviews when changing buyer
            if article.buyer is not None and article.buyer != buyer:
                if Review.objects.filter(review_type="seller", article=article).exists():
                    seller_review = Review.objects.get(review_type="seller", article=article)
                    seller_review.delete()
                if Review.objects.filter(review_type="buyer", article=article).exists():
                    buyer_review = Review.objects.get(review_type="buyer", article=article)
                    buyer_review.delete()
            
            article.buyer = buyer
            article.sold_at = timezone.now()
            article.save()
            
            
        elif self.request.method == "DELETE":
            
            # delete reviews when deleting buyer
            if Review.objects.filter(review_type="seller", article=article).exists():
                seller_review = Review.objects.get(review_type="seller", article=article)
                seller_review.delete()
            if Review.objects.filter(review_type="buyer", article=article).exists():
                buyer_review = Review.objects.get(review_type="buyer", article=article)
                buyer_review.delete()
                
            article.buyer = None
            article.sold_at = None
            article.save()
            
        return Response(
            ArticleSerializer(
                article, context={"user": request.user},
            ).data,
            status=status.HTTP_200_OK,
        )

    def destroy(self, request, pk=None):
        if Article.objects.filter(id=pk).exists():
            article = Article.objects.get(id=pk)
        else:
            return Response({"해당하는 게시글을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        if article.seller != request.user:
            return Response(
                {"작성자 외에는 게시글을 삭제할 수 없습니다."}, status=status.HTTP_403_FORBIDDEN
            )

        article.delete()
        return Response({"success": True}, status=status.HTTP_200_OK)

    def list(self, request):
        user = request.user
        page_id = request.GET.get("page", None)
        category = request.GET.get("category", None)
        keyword = request.GET.get("keyword", None)
        category_list = [
            "디지털기기",
            "가구/인테리어",
            "생활/가공식품",
            "스포츠/레저",
            "여성의류",
            "게임/취미",
            "반려동물용품",
            "식물",
            "삽니다",
            "생활가전",
            "유아동",
            "유아도서",
            "여성잡화",
            "남성패션/잡화",
            "뷰티/미용",
            "도서/티켓/음반",
            "기타 중고물품",
        ]
        user_category_list = []

        # filter article of neighborhood
        neighborhood = [user.location.id]
        for location_neighborhood in user.location.neighborhoods.all():
            neighborhood.append(location_neighborhood.neighborhood.id)
        articles = self.queryset.filter(Q(location__id__in=neighborhood)&Q(seller__is_active=True))

        if not keyword:
            # check categories to filter article
            if not category:
                for i, enable in enumerate(list(user.interest)):
                    if enable == "1":
                        user_category_list.append(category_list[i])
            else:
                if category in category_list:
                    user_category_list.append(category)
                else:
                    return Response(
                        data="올바른 카테고리를 지정해주세요.", status=status.HTTP_400_BAD_REQUEST
                    )
            # filter article by category
            articles = articles.filter(category__in=user_category_list)
        else:
            # filter article by keyword
            articles = articles.filter(title__contains=keyword)

        articles = articles.order_by("-created_at")
        pages = Paginator(articles, 15)

        # check if page_id is valid
        if not page_id:
            return Response(
                ArticleSerializer(
                    articles, many=True, context={"user" : request.user},
                ).data, 
                status=status.HTTP_200_OK,
            )
        serializer = ArticlePaginationValidator(
            data={"page_id": page_id, "article_num": articles.count()}
        )
        serializer.is_valid(raise_exception=True)

        if articles.count() == 0:
            return Response(status=status.HTTP_200_OK)

        page_id = serializer.data.get("page_id")
        return Response(
            ArticleSerializer(
                pages.page(page_id), many=True, context={"user": request.user},
            ).data,
            status=status.HTTP_200_OK,
        )

    def retrieve(self, request, pk=None):
        if Article.objects.filter(Q(id=pk)&Q(seller__is_active=True)).exists():
            article = Article.objects.get(id=pk)
        else:
            return Response({"해당하는 게시글을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        if article.seller == request.user:
            return Response(ArticleSerializer(article, context={"user": request.user}).data, status=status.HTTP_200_OK)
        
        article_id = pk
        user_id = request.user.id
        cookie_value = request.COOKIES.get("hit", "_")
        expire_date, now = datetime.now() + timedelta(hours=1), datetime.now()
        expire_date = expire_date.replace(minute=0, second=0, microsecond=0)
        expire_date -= now
        max_age = expire_date.total_seconds()
        
        if "_{%s}&{%s}_"%(article_id, user_id) not in cookie_value :
            article.hit += 1
            article.save()
            cookie_value += "{%s}&{%s}_"%(article_id, user_id)
            response = Response(ArticleSerializer(article, context={"user": request.user}).data, status=status.HTTP_200_OK)
            response.set_cookie("hit", value=cookie_value, max_age=max_age, httponly=True)
            return response
        else:
            return Response(ArticleSerializer(article, context={"user": request.user}).data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=["PUT"])
    def like(self, request, pk):
        if Article.objects.filter(id=pk).exists():
            article = Article.objects.get(id=pk)
        else:
            return Response({"해당하는 게시글을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        user = request.user
        
        if self.request.method == "PUT":
            if article.liked_users.filter(pk=user.id).exists():
                article.liked_users.remove(user)
                article.like -= 1
                article.save()
            else:
                article.liked_users.add(user)
                article.like += 1
                article.save()
            return Response(
                ArticleSerializer(
                    article, context={"user": request.user}
                ).data, 
                status=status.HTTP_200_OK
            )

    @action(detail=True, methods=["POST", "GET"])
    def comment(self, request, pk):
        if Article.objects.filter(id=pk).exists():
            article = Article.objects.get(id=pk)
        else:
            return Response({"해당하는 게시글을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        if self.request.method == "POST":
            serializer = CommentCreateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.create(serializer.validated_data, request.user, article)
            comments = Comment.objects.filter(article=article)
            return Response(
                CommentSerializer(
                    comments, many=True, context={"user": request.user}
                ).data,
                status=status.HTTP_201_CREATED,
            )

        elif self.request.method == "GET":
            comments = Comment.objects.filter(article=article)
            return Response(
                CommentSerializer(
                    comments, many=True, context={"user": request.user}
                ).data,
                status=status.HTTP_200_OK,
            )


class CommentView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def delete(self, request, a_id, c_id):
        if Article.objects.filter(id=a_id).exists():
            article = Article.objects.get(id=a_id)
        else:
            return Response({"해당하는 게시글을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        if Comment.objects.filter(id=c_id, article=article).exists():
            comment = Comment.objects.get(id=c_id, article=article)
        else:
            return Response({"해당하는 댓글을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        if comment.commenter != request.user:
            return Response(
                {"작성자 외에는 댓글을 삭제할 수 없습니다."}, status=status.HTTP_403_FORBIDDEN
            )

        comment.deleted_at = timezone.now()
        comment.save()
        comments = Comment.objects.filter(article=article)
        return Response(
            CommentSerializer(comments, many=True, context={"user": request.user}).data,
            status=status.HTTP_200_OK,
        )

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
        comments = Comment.objects.filter(article=article)
        return Response(
            CommentSerializer(comments, many=True, context={"user": request.user}).data,
            status=status.HTTP_201_CREATED,
        )
