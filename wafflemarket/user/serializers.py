import os
import re
import time
import datetime
import urllib.request

from rest_framework import serializers
from rest_framework_jwt.settings import api_settings

from django.contrib.auth import get_user_model
from django.contrib.auth.models import update_last_login
from django.core.files import File
from django.utils import timezone

from user.models import User, Auth
from location.serializers import LocationSerializer
from article.models import Article
from review.services import update_temparature


User = get_user_model()
JWT_PAYLOAD_HANDLER = api_settings.JWT_PAYLOAD_HANDLER
JWT_ENCODE_HANDLER = api_settings.JWT_ENCODE_HANDLER


def jwt_token_of(user):
    payload = JWT_PAYLOAD_HANDLER(user)
    jwt_token = JWT_ENCODE_HANDLER(payload)
    return jwt_token


class UserAuthSerializer(serializers.Serializer):
    phone_number = serializers.CharField(required=True)

    def validate(self, data):
        p = re.compile((r"^\d{2,3}\d{3,4}\d{4}$"))
        phone_number = data.get("phone_number")
        if phone_number is None:
            raise serializers.ValidationError("전화번호가 입력되지 않았어요.")
        elif p.match(phone_number) is None:
            raise serializers.ValidationError("전화번호가 올바르지 않아요.")
        else:
            return data

    def create(self, validated_data):
        phone_number = validated_data.get("phone_number")
        if Auth.objects.filter(phone_number=phone_number).exists():
            auth = Auth.objects.get(phone_number=phone_number)
        else:
            auth = Auth.objects.create(**validated_data)
        auth.create_auth_number()
        return auth

    def authenticate(self, data):
        phone_number = data.get("phone_number")
        auth_number = data.get("auth_number")
        if Auth.objects.filter(
            phone_number=phone_number, auth_number=auth_number
        ).exists():
            return True
        else:
            return False


class UserCreateSerializer(serializers.Serializer):
    phone_number = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    username = serializers.CharField(required=True)
    profile_image = serializers.ImageField(allow_empty_file=True, required=False)
    password = serializers.CharField(required=False)
    is_superuser = serializers.BooleanField(required=False, default=False)
    is_staff = serializers.BooleanField(required=False, default=False)

    def validate(self, data):
        phone_number = data.get("phone_number")
        email = data.get("email")
        if phone_number is None and email is None:
            raise serializers.ValidationError("전화번호와 이메일 중 하나는 필수로 입력되어야 합니다.")

        p = re.compile(r"^\d{2,3}\d{3,4}\d{4}$")
        if phone_number is not None and p.match(phone_number) is None:
            raise serializers.ValidationError("전화번호가 올바르지 않아요.")

        u = re.compile((r"^[^&=_\'-+,<>]+$"))
        username = data.get("username")
        if username is not None and u.match(username) is None:
            raise serializers.ValidationError("올바른 닉네임을 입력해주세요.")

        return data

    def create(self, validated_data):
        is_staff = validated_data.get("is_staff")
        is_superuser = validated_data.get("is_superuser")
        password = validated_data.get("password")
        profile_image = validated_data.get("profile_image")

        if is_staff == True and is_superuser == True and password:
            user = User.objects.create_superuser(**validated_data)
        else:
            user = User.objects.create_user(**validated_data)

        # profile image is necessary
        if not profile_image:
            try:
                defalut_image_url = (
                    "https://"
                    + os.getenv("AWS_S3_BUCKET")
                    + ".s3.ap-northeast-2.amazonaws.com/default_image/user_profile.jpeg"
                )
                result = urllib.request.urlretrieve(defalut_image_url)
                image_file = File(open(result[0], "rb"))
                image_file.content_type = "image/jpeg"
                user.profile_image.save(os.path.basename(defalut_image_url), image_file)
            except:
                pass
        user.save()
                
        return user, jwt_token_of(user)


class UserLoginSerializer(serializers.Serializer):

    phone_number = serializers.CharField(max_length=64, required=False)
    email = serializers.EmailField(max_length=255, required=False)
    token = serializers.CharField(max_length=255, read_only=True)

    def validate(self, data):
        phone_number = data.get("phone_number")
        email = data.get("email")
        user = self.find_user(phone_number, email)
        user_data = UserSerializer(user).data
        update_last_login(None, user)
        
        return {
            "logined" : True,
            "user" : user_data,
            "token": jwt_token_of(user),
            "first_login" : self.check_first_login(data=data),
            "location_exists" : self.location_exists(data=data),
        }

    def find_user(self, phone_number, email):
        if phone_number and User.objects.filter(
            phone_number=phone_number, is_active=True
        ):
            return User.objects.get(phone_number=phone_number, is_active=True)
        elif email and User.objects.filter(email=email, is_active=True):
            return User.objects.get(email=email, is_active=True)
        else:
            raise serializers.ValidationError("존재하지 않는 사용자입니다.")

    def check_first_login(self, data):
        phone_number = data.get("phone_number")
        email = data.get("email")
        user = self.find_user(phone_number, email)

        if user.last_login is None:
            return True
        elif user.last_login is not None:
            return False

    def location_exists(self, data):
        phone_number = data.get("phone_number")
        email = data.get("email")
        user = self.find_user(phone_number, email)

        if user.location is None:
            return False
        elif user.location is not None:
            return True


class UserSerializer(serializers.ModelSerializer):
    profile_image = serializers.SerializerMethodField(read_only=True)
    location = serializers.SerializerMethodField(read_only=True)
    article_cnt = serializers.SerializerMethodField(read_only=True)
    temparature = serializers.SerializerMethodField(read_only=True)
    created_at = serializers.SerializerMethodField(read_only=True)
    last_login = serializers.SerializerMethodField(read_only=True)
    leaved_at = serializers.SerializerMethodField(read_only=True)
    username_changed_at = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "phone_number",
            "username",
            "profile_image",
            "email",
            "temparature",
            "created_at",
            "last_login",
            "leaved_at",
            "username_changed_at",
            "is_active",
            "location",
            "article_cnt",
        )

    def get_profile_image(self, user):
        if not user.profile_image:
            return None
        url = user.profile_image.url
        if url.find("?") == -1:
            return url
        return url[: url.find("?")]

    def get_location(self, user):
        if user.location is None:
            return None
        return LocationSerializer(user.location, context=self.context).data

    def get_article_cnt(self, user):
        article_cnt = Article.objects.filter(seller=user).count()
        return article_cnt
    
    def get_temparature(self, user):
        update_temparature(user)
        return user.temparature

    def get_created_at(self, user):
        if user.created_at is not None:
            return time.mktime(user.created_at.timetuple())-54000
        else:
            return None

    def get_last_login(self, user):
        if user.last_login is not None:
            return time.mktime(user.last_login.timetuple())-54000
        else:
            return None

    def get_leaved_at(self, user):
        if user.leaved_at is not None:
            return time.mktime(user.leaved_at.timetuple())-54000
        else:
            return None

    def get_username_changed_at(self, user):
        if user.username_changed_at is not None:
            return time.mktime(user.username_changed_at.timetuple())-54000
        else:
            return None

class UserSimpleSerializer(serializers.ModelSerializer):
    location = serializers.SerializerMethodField(read_only=True)
    article_cnt = serializers.SerializerMethodField(read_only=True)
    profile_image = serializers.SerializerMethodField(read_only=True)
    temparature = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "location",
            "article_cnt",
            "profile_image",
            "temparature",
        )

    def get_location(self, user):
        if user.location is None:
            return None
        return LocationSerializer(user.location, context=self.context).data

    def get_article_cnt(self, user):
        article_cnt = Article.objects.filter(seller=user).count()
        return article_cnt

    def get_profile_image(self, user):
        if not user.profile_image:
            return None
        url = user.profile_image.url
        if url.find("?") == -1:
            return url
        return url[: url.find("?")]
    
    def get_temparature(self, user):
        update_temparature(user)
        return user.temparature


class UserUpdateSerializer(serializers.Serializer):
    username = serializers.CharField(required=False)
    profile_image = serializers.ImageField(required=False)

    def validate(self, data):
        u = re.compile((r"^[^&=_\'-+,<>]+$"))
        username = data.get("username")
        if username is not None and u.match(username) is None:
            raise serializers.ValidationError("올바른 닉네임을 입력해주세요.")

        return data

    def check_username(self, request_data):
        data = request_data["data"]
        user = request_data["user"]
        time_limit = timezone.now() - datetime.timedelta(days=30)
        username = data.get("username")
        if (
            username is not None
            and username != user.username
            and user.username_changed_at is not None
        ):
            if user.username_changed_at > time_limit:
                raise serializers.ValidationError("최근 30일 내 닉네임을 수정한 적이 있어요.")
        return data

    def update(self, user, validated_data):
        username = validated_data.get("username")
        if username != user.username and username is not None:
            user.username = username
            user.username_changed_at = timezone.now()
            user.save()
        return user


class UserCategorySerializer(serializers.Serializer):
    category = serializers.CharField(required=True)
    enabled = serializers.BooleanField(required=True)

    def validate(self, data):
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

        if category not in category_list:
            raise serializers.ValidationError("카테고리가 부적절해요.")
        return data

    def update(self, user, validated_data):
        category = validated_data.get("category")
        enabled = validated_data.get("enabled")
        category_code = {
            "디지털기기": 0,
            "가구/인테리어": 1,
            "생활/가공식품": 2,
            "스포츠/레저": 3,
            "여성의류": 4,
            "게임/취미": 5,
            "반려동물용품": 6,
            "식물": 7,
            "삽니다": 8,
            "생활가전": 9,
            "유아동": 10,
            "유아도서": 11,
            "여성잡화": 12,
            "남성패션/잡화": 13,
            "뷰티/미용": 14,
            "도서/티켓/음반": 15,
            "기타 중고물품": 16,
        }
        code = category_code[category]
        if enabled is True:
            enabled = "1"
        else:
            enabled = "0"
        interest = list(user.interest)
        interest[code] = enabled
        user.interest = "".join(interest)
        user.save()