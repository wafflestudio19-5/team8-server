from abc import ABC
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import update_last_login
from rest_framework import serializers
from rest_framework.fields import NullBooleanField
from rest_framework.status import HTTP_400_BAD_REQUEST
from rest_framework_jwt.settings import api_settings
from django.http import HttpResponseBadRequest
from .models import User, Auth
import re
from django.utils import timezone
import datetime
from location.serializers import LocationSerializer

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
        p = re.compile((r'^\d{2,3}\d{3,4}\d{4}$'))
        phone_number = data.get('phone_number')
        if phone_number is None:
            raise serializers.ValidationError("전화번호가 입력되지 않았어요.")
        elif p.match(phone_number) is None:
            raise serializers.ValidationError("전화번호가 올바르지 않아요.")
        else:
            return data
    
    def create(self, validated_data):
        phone_number = validated_data.get('phone_number')
        if Auth.objects.filter(phone_number=phone_number).exists():
            auth = Auth.objects.get(phone_number=phone_number)
        else:
            auth = Auth.objects.create(**validated_data)
        auth.create_auth_number()
        return auth
    
    def authenticate(self, data):
        phone_number = data.get("phone_number")
        auth_number = data.get("auth_number")
        if Auth.objects.filter(phone_number=phone_number, auth_number=auth_number).exists():
            return True
        else:
            return False

class UserCreateSerializer(serializers.Serializer):
    phone_number = serializers.CharField(required=True)
    username = serializers.CharField(required=True)
    profile_image = serializers.ImageField(required=False)
    is_staff = serializers.BooleanField(required=False)

    def validate(self, data):
        p = re.compile(r'^\d{2,3}\d{3,4}\d{4}$')
        phone_number = data.get('phone_number')
        if phone_number is None:
            raise serializers.ValidationError("전화번호가 입력되지 않았어요.")
        elif p.search(phone_number) is None:
            raise serializers.ValidationError("전화번호가 올바르지 않아요.")      
        
        u = re.compile((r'^[가-힣a-zA-Z0-9]+$'))
        username = data.get('username')
        if username is not None and u.match(username) is None:
            raise serializers.ValidationError("닉네임은 띄어쓰기 없이 영문 한글 숫자만 가능해요.")
        
        return data

    def create(self, validated_data):
        is_staff = validated_data.get('is_staff')
        if is_staff==False:
            user = User.objects.create_superuser(**validated_data)
        user = User.objects.create_user(**validated_data)
        user.save()
        return user, jwt_token_of(user)
    

class UserLoginSerializer(serializers.Serializer):

    phone_number = serializers.CharField(max_length=64, required=True)
    token = serializers.CharField(max_length=255, read_only=True)

    def validate(self, data):
        phone_number = data.get('phone_number')
        
        if User.objects.filter(phone_number=phone_number, is_active=True):
            user = User.objects.get(phone_number = phone_number, is_active=True)
        else:
            raise serializers.ValidationError("가입되지 않은 사용자입니다.")
        
        update_last_login(None, user)
        return {
            'phone_number': user.phone_number,
            'username' : user.username,
            'token': jwt_token_of(user)
        }
    
    def check_first_login(self, data):
        phone_number = data.get('phone_number')
        if User.objects.filter(phone_number=phone_number, is_active=True):
            user = User.objects.get(phone_number=phone_number, is_active=True)
        else:
            raise serializers.ValidationError("존재하지 않는 사용자입니다.")
        
        if user.last_login is None:
            return True
        elif user.last_login is not None:
            return False
    
    def location_exists(self, data):
        phone_number = data.get('phone_number')
        if User.objects.filter(phone_number=phone_number, is_active=True):
            user = User.objects.get(phone_number=phone_number, is_active=True)
        else:
            raise serializers.ValidationError("존재하지 않는 사용자입니다.")
        
        if user.location is None:
            return False
        elif user.location is not None:
            return True
    
        

