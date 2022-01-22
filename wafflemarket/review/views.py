from xml.dom import VALIDATION_ERR
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from django.db import IntegrityError
from django.shortcuts import render

from .models import Review, Temparature
from .serializers import ReviewArticleSerializer, ReviewArticleValidator
from user.models import User
from article.models import Article


class ReviewArticleViewSet(viewsets.GenericViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ReviewArticleSerializer
    queryset = Review.objects.all()
        
    @action(detail=True, methods=["GET", "DELETE",])
    def sent(self, request, pk):
        if Article.objects.filter(pk=pk).exists():
            article = Article.objects.get(pk=pk)
        else:
            return Response(
                {"존재하지 않는 게시글입니다."}, status=status.HTTP_404_NOT_FOUND
                )
        if request.user not in [article.seller, article.buyer]:
            return Response(
                {"해당 게시글과 관련된 사용자가 아닙니다."}, status=status.HTTP_403_FORBIDDEN
                )
            
        if self.request.method == "GET":
            if Review.objects.filter(article=article, reviewer=request.user).exists():
                review = Review.objects.get(article=article, reviewer=request.user)
                received = Review.objects.filter(article=article, reviewyee=request.user).exists()
                return Response(
                    ReviewArticleSerializer(review, context={"type" : "sent", "to_view" : ("received", received)}).data, status=status.HTTP_200_OK
                    )
            else:
                return Response(
                    {"리뷰를 조회 혹은 삭제할 수 없습니다."}, status=status.HTTP_403_FORBIDDEN
                    )

        if self.request.method == "DELETE":
            if Review.objects.filter(article=article, reviewer=request.user).exists():
                review = Review.objects.get(article=article, reviewer=request.user)
                review.delete()
                return Response(
                    {"deleted" : True}, status=status.HTTP_200_OK
                    )
            else:
                return Response(
                    {"리뷰를 조회 혹은 삭제할 수 없습니다."}, status=status.HTTP_403_FORBIDDEN
                    )
        
    @action(detail=True, methods=["GET",])
    def received(self, request, pk):
        if Article.objects.filter(pk=pk).exists():
            article = Article.objects.get(pk=pk)
        else:
            return Response(
                {"존재하지 않는 게시글입니다."}, status=status.HTTP_404_NOT_FOUND
                )
            
        if self.request.method == "GET":
            if Review.objects.filter(article=article, reviewyee=request.user).exists():
                if(article.seller==request.user):
                    review = Review.objects.get(article=article, reviewer=article.buyer, reviewyee=request.user)
                elif(article.buyer==request.user):
                    review = Review.objects.get(article=article, reviewer=article.seller, reviewyee=request.user)
                else:
                    return Response(
                        {"해당 게시글과 관련된 사용자가 아닙니다."}, status=status.HTTP_403_FORBIDDEN
                        )
                sent = Review.objects.filter(article=article, reviewer=request.user).exists()
                return Response(
                    ReviewArticleSerializer(review, context={"type" : "received", "to_view" : ("sent", sent)}).data, status=status.HTTP_200_OK
                    )
            else:
                return Response(
                    {"리뷰를 조회 혹은 삭제할 수 없습니다."}, status=status.HTTP_403_FORBIDDEN
                    )
                
    @action(detail=True, methods=["POST",])
    def seller(self, request, pk):
        if Article.objects.filter(pk=pk).exists():
            article = Article.objects.get(pk=pk)
        else:
            return Response(
                {"존재하지 않는 게시글입니다."}, status=status.HTTP_404_NOT_FOUND
                )
        if article.seller != request.user or article.sold_at is None:
            return Response(
                    {"리뷰를 작성할 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN
                    )
        if Review.objects.filter(article=article, reviewer=request.user):
            return Response(
                {"하나의 거래글 당 하나의 후기만 작성할 수 있습니다."}, status=status.HTTP_403_FORBIDDEN
                )
        
        review = request.data.get('review', None)
        if review is not None: 
            review_location = request.user.location
        else:
            review_location = None
            
        serializer = ReviewArticleValidator(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        review = Review(review_type="seller", 
                        reviewer=article.seller, 
                        reviewyee=article.buyer,
                        article=article, 
                        review_location = review_location,
                        **serializer.validated_data
                        )
        review.save()
        received = Review.objects.filter(article=article, reviewyee=request.user).exists()
        return Response(
                ReviewArticleSerializer(review, context={"type" : "sent", "to_view" : ("received", received)}).data, {"success" : True}, status=status.HTTP_201_CREATED
                )
        
        
    @action(detail=True, methods=["POST",]) 
    def buyer(self, request, pk):
        if Article.objects.filter(pk=pk).exists():
            article = Article.objects.get(pk=pk)
        else:
            return Response(
                {"존재하지 않는 게시글입니다."}, status=status.HTTP_404_NOT_FOUND
                )
        if article.buyer != request.user:
            return Response(
                    {"리뷰를 작성할 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN
                    )
        if Review.objects.filter(article=article, reviewer=request.user):
            return Response(
                {"하나의 거래글 당 하나의 후기만 작성할 수 있습니다."}, status=status.HTTP_403_FORBIDDEN
                )
        
        review = request.data.get('review', None)
        if review is not None: 
            review_location = request.user.location
        else:
            review_location = None
            
        serializer = ReviewArticleValidator(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        review = Review(review_type="buyer", 
                        reviewer=article.buyer, 
                        reviewyee=article.seller,
                        article=article, 
                        review_location = review_location,
                        **serializer.validated_data
                        )
        review.save()
        received = Review.objects.filter(article=article, reviewyee=request.user).exists()
        return Response(
                ReviewArticleSerializer(review, context={"type" : "sent", "to_view" : ("received", received)}).data, status=status.HTTP_201_CREATED
                )
    
'''        
class ReviewUserViewSet(viewsets.GenericViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = UserSerializer
    queryset = User.objects.all()
    
    def retrieve(self, request, pk):
    
    @action(detail=True, methods=["POST", "PUT", "GET",]) #response: 보낸 후기 serializing
    def manner(self, request, pk):
        
    @action(detail=True, methods=["GET",]) #response: 보낸 후기 serializing
    def review(self, request):
        
    @action(detail=True, methods=["GET",]) #response: 보낸 후기 serializing
    def review(self, request):
        
    @action(detail=True, methods=["POST",]) #response: 보낸 후기 serializing
    def buyer(self, request, pk):
        
    @action(detail=True, methods=["GET", "DELETE",])
    def sent(self, request, pk):'''