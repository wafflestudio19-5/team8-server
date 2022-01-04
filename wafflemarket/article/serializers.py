from abc import ABC
from rest_framework import serializers
from .models import Article
from user.models import User
from user.serializers import UserSimpleSerializer


class ArticleCreateSerializer(serializers.Serializer):
    title = serializers.CharField(required=True)
    content = serializers.CharField(required=True)
    product_image = serializers.ImageField(required=False)
    category = serializers.CharField(required=True)
    price = serializers.IntegerField(required=False)

    def validate(self, data):
        price = data.get('price')
        title = data.get('title')
        content = data.get('content')
        category = data.get('category')
        category_list = ['디지털기기', '가구/인테리어', '생활/가공식품', '스포츠/레저', '여성의류', '게임/취미', '반려동물용품', '식물',
                         '삽니다', '생활가전', '유아동', '유아도서', '여성잡화', '남성패션/잡화', '뷰티/미용', '도서/티켓/음반', '기타 중고물품']
        
        if not str(price).isdigit():
            raise serializers.ValidationError("가격은 0 이상의 정수로 입력되어야 해요.")
        if not title.replace(" ", ""):
            raise serializers.ValidationError("제목에는 공백이 아닌 텍스트가 포함되어야 해요.")
        if not content.replace(" ", ""):
            raise serializers.ValidationError("내용에는 공백이 아닌 텍스트가 포함되어야 해요.")
        if category not in category_list:
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
    buyer = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Article
        fields = (
            'id',
            'seller',
            'location',
            'title',
            'content',
            #'product_image',
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
        #return LocationSerializer(user.location, context=self.context).data
        return "미완"
    def get_buyer(self, article):
        if article.buyer is None:
            return "거래중"
        else:
            return UserSimpleSerializer(article.buyer, context=self.context).data