from xml.dom import VALIDATION_ERR
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from django.db.models import Q

from .models import Review
from .serializers import ReviewArticleSerializer, ReviewArticleValidator, ReviewUserSerializer, ReviewUserValidator, ReviewSerializer, UserReviewSerializer
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
    

class ReviewUserView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def put(self, request, user_id, type):
        if User.objects.filter(pk=user_id).exists():
            reviewyee = User.objects.get(pk=user_id)
        else:
            return Response(
                {"존재하지 않는 사용자입니다."}, status=status.HTTP_404_NOT_FOUND
                )
        reviewer = request.user
        serializer = ReviewUserValidator(data=request.data, context={"manner_type" : type})
        serializer.is_valid(raise_exception=True)
        
        if Review.objects.filter(review_type="user", reviewer=reviewer, reviewyee=reviewyee, manner_type=type).exists():
            review = Review.objects.get(review_type="user", reviewer=reviewer, reviewyee=reviewyee, manner_type=type)
            review = serializer.update_manner(review, request.data)
            return Response(
                ReviewUserSerializer(review).data, status=status.HTTP_200_OK
                )
        else:
            review = Review(review_type="user", 
                            reviewer=reviewer, 
                            reviewyee=reviewyee,
                            article=None, 
                            review = None,
                            review_location = None,
                            manner_type = type,
                            **serializer.validated_data
                            )
            review.save()
            review = Review.objects.get(review_type="user", reviewer=reviewer, reviewyee=reviewyee, manner_type=type)
            return Response(
                ReviewUserSerializer(review).data, status=status.HTTP_201_CREATED
                )
       
        
    def get(self, request, user_id, type):
        if User.objects.filter(pk=user_id).exists():
            reviewyee = User.objects.get(pk=user_id)
        else:
            return Response(
                {"존재하지 않는 사용자입니다."}, status=status.HTTP_404_NOT_FOUND
                )
        reviewer = request.user
        if type=="good":
            manner = "0"*3
        elif type=="bad":
            manner = "0"*2
        else:
            return Response(
                {"매너칭찬, 비매너평가 중 하나를 선택해야 합니다."}, status-status.HTTP_400_BAD_REQUEST
            )
            
        if Review.objects.filter(review_type="user", reviewer=reviewer, reviewyee=reviewyee, manner_type=type).exists():
            review = Review.objects.get(review_type="user", reviewer=reviewer, reviewyee=reviewyee, manner_type=type)
            return Response(
                ReviewUserSerializer(review).data, status=status.HTTP_200_OK
                )
            
        else:
            review = Review(review_type="user", 
                            reviewer=reviewer, 
                            reviewyee=reviewyee,
                            article=None, 
                            review = None,
                            review_location = None,
                            manner_type=type,
                            manner = manner
                            )
            review.save()
            review = Review.objects.get(review_type="user", reviewer=reviewer, reviewyee=reviewyee, manner_type=type)
            return Response(
                ReviewUserSerializer(review).data, status=status.HTTP_201_CREATED
                )
    
class ReviewViewSet(viewsets.GenericViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ReviewUserSerializer
    queryset = Review.objects.all()
    
    code_good_manner = {
            0 : "친절하고 매너가 좋아요.",
            1 : "시간 약속을 잘 지켜요.",
            2 : "응답이 빨라요.",
            
            3 : "상품상태가 설명한 것과 같아요.",
            4 : "나눔을 해주셨어요.",
            5 : "상품설명이 자세해요.",
            6 : "좋은 상품을 저렴하게 판매해요.",
            
            7 :"제가 있는 곳까지 와서 거래했어요.",
    }
    
    good_manner_cnt = {
            "친절하고 매너가 좋아요." : set(),
            "시간 약속을 잘 지켜요." : set(),
            "응답이 빨라요." : set(),
            
            "상품상태가 설명한 것과 같아요." : set(),
            "나눔을 해주셨어요." : set(),
            "상품설명이 자세해요." : set(),
            "좋은 상품을 저렴하게 판매해요." : set(),
            
            "제가 있는 곳까지 와서 거래했어요." : set(),
        } 

    @action(detail=True, methods=["GET",])
    def review(self, request, pk):
        if User.objects.filter(pk=pk).exists():
            reviewyee = User.objects.get(pk=pk)
        else:
            return Response(
                {"존재하지 않는 사용자입니다."}, status=status.HTTP_404_NOT_FOUND
                )
        reviews = Review.objects.filter(Q(review_type="seller") | Q(review_type="buyer"), reviewyee=reviewyee)
        return Response(ReviewSerializer(reviews, many=True).data, status=status.HTTP_200_OK)
    
    
    @action(detail=True, methods=["GET",])
    def manner(self, request, pk):
        if User.objects.filter(pk=pk).exists():
            reviewyee = User.objects.get(pk=pk)
        else:
            return Response(
                {"존재하지 않는 사용자입니다."}, status=status.HTTP_404_NOT_FOUND
                )
        
        reviews = Review.objects.filter(reviewyee=reviewyee, manner_type="good").all()
        for review in reviews:
            manner = review.manner
            reviewer = review.reviewer
            for i, v in enumerate(manner):
                if v=="1":
                    self.good_manner_cnt[self.code_good_manner[i]].add(reviewer)
        for manner in self.good_manner_cnt:
            self.good_manner_cnt[manner] = len(self.good_manner_cnt[manner])
        return Response(self.good_manner_cnt, status=status.HTTP_200_OK)
    
    
    def retrieve(self, request, pk):
        if User.objects.filter(pk=pk).exists():
            user = User.objects.get(pk=pk)
        else:
            Response(
                {"존재하지 않는 사용자입니다."}, status=status.HTTP_404_NOT_FOUND
                )
        return Response(UserReviewSerializer(user).data, status=status.HTTP_200_OK)