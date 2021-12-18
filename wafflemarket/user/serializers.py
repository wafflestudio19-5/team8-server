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

User = get_user_model()
JWT_PAYLOAD_HANDLER = api_settings.JWT_PAYLOAD_HANDLER
JWT_ENCODE_HANDLER = api_settings.JWT_ENCODE_HANDLER

def jwt_token_of(user):
    payload = JWT_PAYLOAD_HANDLER(user)
    jwt_token = JWT_ENCODE_HANDLER(payload)
    return jwt_token

class UserAuthSerializer(serializers.Serializer):
    phone_number = serializers.CharField(required=True)

    def validate(self, data):  ##미완
        phone_number = data.get('phone_number')
        if phone_number is None:
            raise serializers.ValidationError("전화번호가 올바르지 않습니다.")
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
        if Auth.objects.filter(phone_number=phone_number, auth_number=auth_number).exists(): return True
        else: return False

class UserCreateSerializer(serializers.Serializer):
    phone_number = serializers.CharField(required=True)
    username = serializers.CharField(required=True)
    profile_image = serializers.ImageField(required=False)
    is_staff = serializers.BooleanField(required=False)

    def validate(self, data): ##미완
        phone_number = data.get('phone_number')
        if phone_number is None:
            raise serializers.ValidationError("인증 실패")
        return data

    def create(self, validated_data):
        is_staff = validated_data.get('is_staff')
        if is_staff==False:
            user = User.objects.create_superuser(**validated_data)
        user = User.objects.create_user(**validated_data)
        user.save()
        return user, jwt_token_of(user)
    
    def update(self, user, username=None, profile_image=None, **kwargs):
        user.username = username
        user.profile_image = profile_image
        user.save()
        return user
    

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
        

class UserSerializer(serializers.ModelSerializer):
    location = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'phone_number',
            'username',
            'email',
            'created_at',
            'logined_at',  
            'leaved_at',  
            'is_active',
            'location'
        )

    def get_location(self, user): ##미완
        return "location"
    
    def validate(self, data): ##미완
        return data
        


