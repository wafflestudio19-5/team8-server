from django.contrib.auth import authenticate, login, logout, get_user_model
from django.db import IntegrityError
from rest_framework import status, viewsets, permissions
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import UserLoginSerializer, UserCreateSerializer,  UserAuthSerializer, UserSerializer

User = get_user_model()

class UserAuthView(APIView):
    permission_classes = (permissions.AllowAny, )
        
    def post(self, request):
        serializer = UserAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        auth = serializer.save()
        return Response(data={'phone_number' : auth.phone_number, 'auth_number' : auth.auth_number}, status=status.HTTP_200_OK)
    
    def put(self, request):
        serializer = UserAuthSerializer(data=request.data)
        if serializer.authenticate(data=request.data):
            if User.objects.filter(phone_number=request.data['phone_number']).exists():
                serializer = UserLoginSerializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                token = serializer.validated_data['token']
                return Response({'logined': True, 'token': token}, status=status.HTTP_200_OK)
            else:
                return Response(data={'authenticated' : True, 'phone_number' : request.data['phone_number']}, status=status.HTTP_200_OK)
        else:
            return Response(data='인증번호가 일치하지 않습니다.', status=status.HTTP_400_BAD_REQUEST)
        
    
class UserSignUpView(APIView):
    permission_classes = (permissions.AllowAny, )
    def post(self, request, *args, **kwargs):
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user, jwt_token = serializer.save()
        except IntegrityError:
            serializer = UserLoginSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            token = serializer.validated_data['token']
            return Response({'logined': True, 'token': token}, status=status.HTTP_200_OK)
        return Response(data={'user': user.phone_number, 'token': jwt_token}, status=status.HTTP_201_CREATED)


class UserLoginView(APIView):
    permission_classes = (permissions.AllowAny, )

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data['token']
        return Response({'logined': True, 'token': token}, status=status.HTTP_200_OK)
    
class UserLogoutView(APIView):
    permission_classes = (permissions.IsAuthenticated, )
    
    def post(self, request):
        logout(request)
        return Response({'logined': False}, status=status.HTTP_200_OK)
    
class UserLeaveView(APIView):
    permission_classes = (permissions.IsAuthenticated, )

    def delete(self, request):
        request.user.is_active = False
        request.user.save()
        logout(request)
        return Response(data={'leaved': True}, status=status.HTTP_200_OK)
    
    
##미완
'''class UserViewSet(viewsets.GenericViewSet): 
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = UserSerializer
    queryset = User.objects.all()
    
    def get(self, request):
        if request.user.is_anonymous:
            return Response(status=status.HTTP_403_FORBIDDEN, data='먼저 로그인 하세요.')
        user = request.user
        return Response(self.get_serializer(user).data, status=status.HTTP_200_OK)

    def put(self, request):
        if request.user.is_anonymous:
            return Response(status=status.HTTP_403_FORBIDDEN, data='먼저 로그인 하세요.')
        user = request.user
        serializer = UserCreateSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.update(user, serializer.validated_data)
        return Response(self.get_serializer(user).data, status=status.HTTP_200_OK)'''