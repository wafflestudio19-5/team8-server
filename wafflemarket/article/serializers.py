import time

from rest_framework import serializers

from user.serializers import UserSimpleSerializer
from location.serializers import LocationSerializer
from article.models import Article, Comment, ProductImage


class ArticleCreateSerializer(serializers.Serializer):
    title = serializers.CharField(required=True)
    content = serializers.CharField(required=True)
    image_count = serializers.CharField(required=True)
    category = serializers.CharField(required=True)
    price = serializers.IntegerField(required=False)

    def validate(self, data):
        price = data.get("price")
        title = data.get("title")
        content = data.get("content")
        image_count = data.get("image_count")
        category = data.get("category")
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

        if price and not str(price).isdigit():
            raise serializers.ValidationError("가격은 0 이상의 정수로 입력되어야 해요.")
        if category and category not in category_list:
            raise serializers.ValidationError("카테고리가 부적절해요.")
        try:
            count = int(image_count)
            if count <= 0:
                raise serializers.ValidationError("사진 개수는 자연수여야 해요.")
        except:
            raise serializers.ValidationError("사진 개수는 자연수여야 해요.")
        return data

    def create_article(self, validated_data, user):
        validated_data.pop("image_count")
        seller = user
        location = user.location
        article = Article.objects.create(
            seller=seller, location=location, **validated_data
        )
        article.save()
        return article

    def update_article(self, validated_data, article):
        article.update(**validated_data)
        article.save()
        return article


class ArticleSerializer(serializers.ModelSerializer):
    seller = serializers.SerializerMethodField(read_only=True)
    location = serializers.SerializerMethodField(read_only=True)
    delete_enable = serializers.SerializerMethodField(read_only=True)
    product_images = serializers.SerializerMethodField(read_only=True)
    buyer = serializers.SerializerMethodField(read_only=True)
    
    created_at = serializers.SerializerMethodField(read_only=True)
    sold_at = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Article
        fields = (
            "id",
            "seller",
            "location",
            "delete_enable",
            "title",
            "content",
            "product_images",
            "category",
            "price",
            "created_at",
            "sold_at",  # None이면 거래중
            "buyer",  # None이면 거래중
            "like",
        )

    def get_seller(self, article):
        return UserSimpleSerializer(article.seller, context=self.context).data

    def get_location(self, article):
        return LocationSerializer(article.location, context=self.context).data
    
    def get_delete_enable(self, article):
        user = self.context["user"]
        return article.seller == user

    def get_product_images(self, article):
        return ProductImageSerializer(
            article.product_images, many=True, context=self.context
        ).data

    def get_buyer(self, article):
        if article.buyer is None:
            return None
        else:
            return UserSimpleSerializer(article.buyer, context=self.context).data
        
    def get_created_at(self, article):
        if article.created_at is not None:
            return time.mktime(article.created_at.timetuple())-54000
        else:
            return None
        
    def get_sold_at(self, article):
        if article.sold_at is not None:
            return time.mktime(article.sold_at.timetuple())-54000
        else:
            return None


class CommentCreateSerializer(serializers.Serializer):
    content = serializers.CharField(required=True)

    def validate(self, data):
        return data

    def create(self, validated_data, commenter, article, parent=None):
        comment = Comment.objects.create(
            commenter=commenter, article=article, parent=parent, **validated_data
        )
        comment.save()


class CommentSerializer(serializers.ModelSerializer):
    commenter = serializers.SerializerMethodField(read_only=True)
    replies = serializers.SerializerMethodField(read_only=True)
    delete_enable = serializers.SerializerMethodField(read_only=True)
    
    created_at = serializers.SerializerMethodField(read_only=True)
    deleted_at = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Comment
        fields = (
            "id",
            "commenter",
            "delete_enable",
            "content",
            "created_at",
            "deleted_at",
            "replies",
        )

    def get_commenter(self, comment):
        return UserSimpleSerializer(comment.commenter, context=self.context).data

    def get_delete_enable(self, comment):
        user = self.context["user"]
        return comment.commenter == user

    def get_replies(self, comment):
        replies = Comment.objects.filter(parent=comment).order_by("created_at")
        return CommentSerializer(replies, context=self.context, many=True).data
    
    def get_created_at(self, comment):
        if comment.created_at is not None:
            return time.mktime(comment.created_at.timetuple())-54000
        else:
            return None
        
    def get_deleted_at(self, comment):
        if comment.deleted_at is not None:
            return time.mktime(comment.deleted_at.timetuple())-54000
        else:
            return None


class ProductImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField(read_only=True)
    thumbnail_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ProductImage
        fields = (
            "image_url",
            "thumbnail_url",
        )

    def get_image_url(self, object):
        url = object.product_image.url
        if url.find("?") == -1:
            return url
        return url[: url.find("?")]

    def get_thumbnail_url(self, object):
        url = object.product_thumbnail.url
        if url.find("?") == -1:
            return url
        return url[: url.find("?")]


class ArticlePaginationValidator(serializers.Serializer):
    page_id = serializers.IntegerField(required=True)
    article_num = serializers.IntegerField(required=True)

    def validate(self, data):
        page_id = data.get("page_id")
        article_num = data.get("article_num")
        if article_num % 15:
            num_pages = article_num / 15 + 1
        else:
            num_pages = article_num / 15
        if page_id <= 0 or page_id > num_pages:
            raise serializers.ValidationError("페이지 번호가 범위를 벗어났습니다.")
        return data
