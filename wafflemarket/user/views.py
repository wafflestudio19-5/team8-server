import os

from rest_framework import status, viewsets, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from google.auth.transport.requests import Request
from google.oauth2 import id_token

from django.contrib.auth import login, logout, get_user_model
from django.db import IntegrityError
from django.http import HttpResponse
from django.shortcuts import render

import wafflemarket.settings as settings
from user.serializers import (
    UserLoginSerializer,
    UserCreateSerializer,
    UserAuthSerializer,
    UserSerializer,
    UserUpdateSerializer,
    UserSimpleSerializer,
    UserCategorySerializer,
)
from article.models import Article
from article.serializers import ArticleSerializer
from review.models import Review


User = get_user_model()


def login(data):
    serializer = UserLoginSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data


class UserAuthView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = UserAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        auth = serializer.save()
        return Response(
            data={"phone_number": auth.phone_number}, status=status.HTTP_200_OK
        )

    def put(self, request):
        serializer = UserAuthSerializer(data=request.data)
        if serializer.authenticate(data=request.data):
            if User.objects.filter(phone_number=request.data["phone_number"]).exists():
                return Response(login(request.data), status=status.HTTP_200_OK)
            else:
                return Response(
                    data={
                        "authenticated": True,
                        "phone_number": request.data["phone_number"],
                    },
                    status=status.HTTP_200_OK,
                )
        else:
            return Response(data="인증번호가 일치하지 않습니다.", status=status.HTTP_400_BAD_REQUEST)


class UserSignUpView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user, jwt_token = serializer.save()
        except IntegrityError:
            return Response(login(request.data), status=status.HTTP_200_OK)
        return Response(login(request.data), status=status.HTTP_201_CREATED)


class GoogleSigninCallBackApi(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, *args, **kwargs):
        if settings.DEBUG:
            return render(request, "user/logintest.html")
        else:
            return HttpResponse(status=404)

    def post(self, request, *args, **kwargs):
        token = request.data.get("token")
        GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

        # verifying access_token
        try:
            idinfo = id_token.verify_oauth2_token(token, Request(), GOOGLE_CLIENT_ID)
            userid = idinfo["sub"]
        except ValueError:
            return Response(data="올바른 토큰이 아닙니다.", status=status.HTTP_400_BAD_REQUEST)

        # get user information
        username = idinfo.get("family_name", "") + idinfo.get("given_name", "")
        username = username.replace(" ", "").replace("\xad", "")
        profile_data = {"email": idinfo["email"], "username": username}

        # signup or login with given info
        serializer = UserCreateSerializer(data=profile_data)
        serializer.is_valid(raise_exception=True)
        try:
            user, jwt_token = serializer.save()
        except IntegrityError:
            return Response(login(profile_data), status=status.HTTP_200_OK)
        return Response(login(profile_data), status=status.HTTP_201_CREATED)


class UserLogoutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        logout(request)
        return Response({"logined": False}, status=status.HTTP_200_OK)


class UserLeaveView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def delete(self, request):
        # temporarily unactivated
        request.user.is_active = False
        request.user.save()
        logout(request)
        return Response(data={"leaved": True}, status=status.HTTP_200_OK)


class UserViewSet(viewsets.GenericViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = UserSerializer
    queryset = User.objects.all()

    def list(self, request):
        user = request.user
        return Response(self.get_serializer(user).data, status=status.HTTP_200_OK)

    def put(self, request):
        user = request.user
        serializer = UserUpdateSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.check_username(
            {"data": serializer.validated_data, "user": request.user}
        )
        user = serializer.update(user, serializer.validated_data)

        try:
            profile_image = request.FILES["profile_image"]
            user.profile_image = profile_image
            user.save()
        except:
            pass
        return Response(self.get_serializer(user).data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        if pk is not None:
            if User.objects.filter(id=pk).exists():
                user = User.objects.get(id=pk)
                if user == request.user:
                    return Response(
                        self.get_serializer(user).data, status=status.HTTP_200_OK
                    )
                else:
                    return Response(
                        UserSimpleSerializer(user).data, status=status.HTTP_200_OK
                    )
            else:
                return Response(
                    {"해당하는 유저를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND
                )
        else:
            user = request.user
            return Response(self.get_serializer(user).data, status=status.HTTP_200_OK)


class UserCategoryView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @classmethod
    def get_list(cls, user):
        code_category = {
            0: "디지털기기",
            1: "가구/인테리어",
            2: "생활/가공식품",
            3: "스포츠/레저",
            4: "여성의류",
            5: "게임/취미",
            6: "반려동물용품",
            7: "식물",
            8: "삽니다",
            9: "생활가전",
            10: "유아동",
            11: "유아도서",
            12: "여성잡화",
            13: "남성패션/잡화",
            14: "뷰티/미용",
            15: "도서/티켓/음반",
            16: "기타 중고물품",
        }
        interest_list = []
        for code, enabled in enumerate(user.interest):
            if enabled == "1":
                interest_list.append(code_category[code])
        return {"category": interest_list}

    def put(self, request):
        user = request.user
        serializer = UserCategorySerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.update(user, serializer.validated_data)
        data = self.get_list(user)
        return Response(data, status=status.HTTP_200_OK)

    def get(self, request):
        user = request.user
        data = self.get_list(user)
        return Response(data, status=status.HTTP_200_OK)


class UserLikedView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        user = request.user
        article = user.liked_articles.all()
        return Response(
            ArticleSerializer(article, many=True, context = {"user" : request.user}).data, status=status.HTTP_200_OK
        )
         
class UserHistoryView(APIView):
    permission_classes = (permissions.IsAuthenticated, )

    def get(self, request, pk=None):
        if pk==1: #구매내역 : 1
            article = Article.objects.filter(buyer=request.user).order_by('-created_at')
            
        elif pk==2: #판매내역 : 2
            sold = request.query_params.get('sold')
            if sold=='true':
                article = Article.objects.filter(seller=request.user, sold_at__isnull=False).order_by('-created_at')
            elif sold=='false':
                article = Article.objects.filter(seller=request.user, sold_at__isnull=True).order_by('-created_at')
            else:
                article = Article.objects.filter(seller=request.user).order_by('-created_at')
        
        else:
            return Response({"올바른 요청을 보내세요."}, status=status.HTTP_400_BAD_REQUEST)
                
        data = ArticleSerializer(article, many=True, context = {"user" : request.user}).data
        return Response(data, status=status.HTTP_200_OK)
