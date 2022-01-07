from abc import ABC
from rest_framework import serializers
from django.core.paginator import Paginator

from .models import Article
from user.serializers import UserSimpleSerializer
from location.serializers import LocationSimpleSerializer


class ArticleCreateSerializer(serializers.Serializer):
    title = serializers.CharField(required=True)
    content = serializers.CharField(required=True)
    product_image = serializers.ImageField(allow_empty_file=True, required=False)
    category = serializers.CharField(required=True)
    price = serializers.IntegerField(required=False)

    def validate(self, data):
        price = data.get('price')
        title = data.get('title')
        content = data.get('content')
        category = data.get('category')
        category_list = ['디지털기기', '가구/인테리어', '생활/가공식품', '스포츠/레저', '여성의류', '게임/취미', '반려동물용품', '식물',
                         '삽니다', '생활가전', '유아동', '유아도서', '여성잡화', '남성패션/잡화', '뷰티/미용', '도서/티켓/음반', '기타 중고물품']
        
        if price and not str(price).isdigit():
            raise serializers.ValidationError("가격은 0 이상의 정수로 입력되어야 해요.")
        if category and category not in category_list:
            raise serializers.ValidationError("카테고리가 부적절해요.")
        return data
    
    def create_article(self, validated_data, user):
        seller = user
        location = user.location
        article = Article.objects.create(seller=seller, location=location, **validated_data)
        article.save()
        return article
    
    def update_article(self, validated_data, article):
        article.update(**validated_data)
        article.save()
        return article
        
    
class ArticleSerializer(serializers.ModelSerializer):
    seller = serializers.SerializerMethodField(read_only=True)
    location = serializers.SerializerMethodField(read_only=True)
    product_image = serializers.SerializerMethodField(read_only=True)
    buyer = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Article
        fields = (
            'id',
            'seller',
            'location',
            'title',
            'content',
            'product_image',
            'category',
            'price',
            'created_at',
            'sold_at', #None이면 거래중
            'buyer', #None이면 거래중
            'deleted_at'
        )
    
    def get_seller(self, article):
        return UserSimpleSerializer(article.seller, context=self.context).data
    def get_location(self, article):
        return LocationSimpleSerializer(article.location, context=self.context).data
    def get_product_image(self, article):
        if not article.product_image:
            return None
        url = article.product_image.url
        if url.find('?') == -1:
            return url
        return url[:url.find('?')]
    def get_buyer(self, article):
        if article.buyer is None:
            return "거래중"
        else:
            return UserSimpleSerializer(article.buyer, context=self.context).data


class ArticlePaginationValidator(serializers.Serializer):
    page_id = serializers.IntegerField(required=True)
    article_num = serializers.IntegerField(required=True)

    def validate(self, data):
        page_id = data.get('page_id')
        article_num = data.get('article_num')
        if article_num % 15:
            num_pages = article_num/15 + 1
        else:
            num_pages = article_num/15
        if page_id <= 0 or page_id > num_pages:
            raise serializers.ValidationError("페이지 번호가 범위를 벗어났습니다.")
        return data