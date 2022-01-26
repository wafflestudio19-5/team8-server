from rest_framework import serializers

from django.db.models import Q

from user.models import User
from review.models import Review
from location.models import Location
from location.serializers import LocationSerializer
from user.serializers import UserSimpleSerializer

class ReviewArticleValidator(serializers.Serializer):
    review = serializers.CharField(required=False)
    manner_type = serializers.CharField(required=True)
    manner_list = serializers.ListField(child=serializers.CharField(), required=True)
    
    good_manner_code = {
            "친절하고 매너가 좋아요." : 0,
            "시간 약속을 잘 지켜요." : 1,
            "응답이 빨라요." : 2,
            
            "상품상태가 설명한 것과 같아요." : 3,
            "나눔을 해주셨어요." : 4,
            "상품설명이 자세해요." : 5,
            "좋은 상품을 저렴하게 판매해요." : 6,
            
            "제가 있는 곳까지 와서 거래했어요." : 7,
        } 
    bad_manner_code = {
            "반말을 사용해요." : 0,
            "불친절해요." : 1,
            "무조건 택배거래만 하려고 해요." : 2,
            "채팅 메시지를 보내도 답이 없어요." : 3,
            "차에서 내리지도 않고 창문만 열고 거래하려고 해요." : 4,
            "무리하게 가격을 깎아요." : 5,
            "예약만 해놓고 거래 시간을 명확하게 알려주지 않아요." : 6,
            "상품에 대해 자세히 알려주지 않아요." : 7,
            "시간약속을 안 지켜요." : 8,
            "너무 늦은 시간이나 새벽에 연락해요." : 9,
            "구매의사 없이 계속 찔러봐요." : 10,
            "거래 약속을 하고 다른 사람한테 팔았어요." : 11,
            "거래 시간과 장소를 정한 후 거래 직전 취소했어요." : 12,
            "거래 시간과 장소를 정한 후 연락이 안돼요." : 13,
            "약속 장소에 나타나지 않았어요." : 14,
        }
    
    @classmethod
    def create_manner_string(cls, manner_type, manner_list):
        if manner_list is None:
            raise serializers.ValidationError("매너평가를 입력해주세요.")
        
        if manner_type=="good":
            try:
                manner = ["0"]*8
                for i in manner_list:
                    manner[cls.good_manner_code[i]]="1"
            except KeyError:
                raise serializers.ValidationError("올바른 평가를 입력해주세요.")
            
        elif manner_type=="bad":
            try:
                manner = ["0"]*15
                for i in manner_list:
                    manner[cls.bad_manner_code[i]]="1"
            except KeyError:
                raise serializers.ValidationError("올바른 평가를 입력해주세요.")
            
        else:
            raise serializers.ValidationError("매너칭찬, 비매너평가 중 하나를 선택해야 합니다.")
        
        manner = "".join(manner)
        return manner
    
    def validate(self, data):
        review = data.get("review", None)
        manner_type = data.get("manner_type")
        manner_list = data.get("manner_list")
        return {"review" : review,
                "manner_type" : manner_type,
                "manner" : self.create_manner_string(manner_type, manner_list)}
    

class ReviewArticleSerializer(serializers.ModelSerializer):
    evaluation = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    to_view = serializers.SerializerMethodField()
    
    class Meta:
        model = Review
        fields = (
            "review",
            "evaluation",
            "type",
            "to_view",
        )
    
    def get_evaluation(self, review):
        code_good_manner = {
            0 : "친절하고 매너가 좋아요.",
            1 : "시간 약속을 잘 지켜요.",
            2 : "응답이 빨라요.",
            
            3 : "상품상태가 설명한 것과 같아요.",
            4: "나눔을 해주셨어요.",
            5 : "상품설명이 자세해요.",
            6 : "좋은 상품을 저렴하게 판매해요.",
            
            7 : "제가 있는 곳까지 와서 거래했어요.",
        }
        code_bad_manner = {
            0 : "반말을 사용해요.",
            1 : "불친절해요.",
            2 : "무조건 택배거래만 하려고 해요.",
            3 : "채팅 메시지를 보내도 답이 없어요.",
            4 : "차에서 내리지도 않고 창문만 열고 거래하려고 해요.",
            5 : "무리하게 가격을 깎아요.",
            6 : "예약만 해놓고 거래 시간을 명확하게 알려주지 않아요.",
            7 : "상품에 대해 자세히 알려주지 않아요.",
            8 : "시간약속을 안 지켜요.",
            9 : "너무 늦은 시간이나 새벽에 연락해요.",
            10 : "구매의사 없이 계속 찔러봐요.",
            11 : "거래 약속을 하고 다른 사람한테 팔았어요.",
            12 : "거래 시간과 장소를 정한 후 거래 직전 취소했어요.",
            13 : "거래 시간과 장소를 정한 후 연락이 안돼요.",
            14 : "약속 장소에 나타나지 않았어요."
        }
        
        manner_list = []
        manner = review.manner
        
        if review.manner_type=="good":
            for i, v in enumerate(manner):
                if v == "1":
                    manner_list.append(code_good_manner[i])
                    
        elif review.manner_type=="bad":
            for i, v in enumerate(manner):
                if v == "1":
                    manner_list.append(code_bad_manner[i])
                    
        return manner_list
    
    def get_type(self, review):
        return self.context["type"]
    
    def get_to_view(self, review):
        return self.context["to_view"]
    
    
class ReviewUserValidator(serializers.Serializer):
    manner_list = serializers.ListField(child=serializers.CharField())
    
    good_manner_code = {
            "친절하고 매너가 좋아요." : 0,
            "시간 약속을 잘 지켜요." : 1,
            "응답이 빨라요." : 2,
        } 
    
    bad_manner_code = {
            "반말을 사용해요." : 0,
            "불친절해요." : 1,
        }
    
    @classmethod
    def create_manner_string(cls, manner_type, manner_list):
        if manner_list is None:
            raise serializers.ValidationError("매너평가를 입력해주세요.")
        
        if manner_type=="good":
            try:
                manner = ["0"]*3
                for i in manner_list:
                    manner[cls.good_manner_code[i]]="1"
            except KeyError:
                raise serializers.ValidationError("올바른 평가를 입력해주세요.")
            
        elif manner_type=="bad":
            try:
                manner = ["0"]*2
                for i in manner_list:
                    manner[cls.bad_manner_code[i]]="1"
            except KeyError:
                raise serializers.ValidationError("올바른 평가를 입력해주세요.")
            
        else:
            raise serializers.ValidationError("매너칭찬, 비매너평가 중 하나를 선택해야 합니다.")
        
        manner = "".join(manner)
        return manner
    
    @classmethod
    def update_manner_string(cls, manner_type, manner, manner_list):
        if manner_list is None:
            raise serializers.ValidationError("매너평가를 입력해주세요.")
        manner = list(manner)
        
        if manner_type=="good":
            for i in range(0, 3):
                manner[i]="0"
            try:
                for i in manner_list:
                    manner[cls.good_manner_code[i]]="1"
            except KeyError:
                raise serializers.ValidationError("올바른 평가를 입력해주세요.")
            
        elif manner_type=="bad":
            for i in range(0, 2):
                manner[i]="0"
            try:
                for i in manner_list:
                    manner[cls.bad_manner_code[i]]="1"
            except KeyError:
                raise serializers.ValidationError("올바른 평가를 입력해주세요.")
            
        else:
            raise serializers.ValidationError("매너칭찬, 비매너평가 중 하나를 선택해야 합니다.")
        
        manner = "".join(manner)
        return manner
    
    def validate(self, data):
        manner_type = self.context["manner_type"]
        manner_list = data.get("manner_list")
        return {"manner" : self.create_manner_string(manner_type, manner_list)}
    
    def update_manner(self, review, data):
        manner_type = review.manner_type
        manner = review.manner
        manner_list = data.get("manner_list")
        manner = self.update_manner_string(manner_type, manner, manner_list)
        
        review.manner = manner
        review.save()
        return review
    
class ReviewUserSerializer(serializers.ModelSerializer):
    evaluation = serializers.SerializerMethodField()
    
    class Meta:
        model = Review
        fields = (
            "manner_type",
            "evaluation",
        )
    
    def get_evaluation(self, review):
        code_good_manner = {
            0 : "친절하고 매너가 좋아요.",
            1 : "시간 약속을 잘 지켜요.",
            2 : "응답이 빨라요.",
        }
        code_bad_manner = {
            0 : "반말을 사용해요.",
            1 : "불친절해요.",
        }
        
        manner_list = []
        manner = review.manner
        
        if review.manner_type=="good":
            for i, v in enumerate(manner[0:3]):
                if v == "1":
                    manner_list.append(code_good_manner[i])
                    
        elif review.manner_type=="bad":
            for i, v in enumerate(manner[0:2]):
                if v == "1":
                    manner_list.append(code_bad_manner[i])
                    
        return manner_list
    
    
class ReviewSerializer(serializers.ModelSerializer):
    reviewer = serializers.SerializerMethodField()
    review_location = serializers.SerializerMethodField()
    
    class Meta:
        model = Review
        fields = (
            "reviewer",
            "review_location",
            "review",
            "review_type",
        )
    
    def get_reviewer(self, review):
        return UserSimpleSerializer(review.reviewer).data
    def get_review_location(self, review):
        return LocationSerializer(review.review_location).data
    
    
class UserMannerSerializer(serializers.ModelSerializer):
    manner = serializers.SerializerMethodField()
    
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
    
    good_manner_list = [
            "친절하고 매너가 좋아요.",
            "시간 약속을 잘 지켜요.",
            "응답이 빨라요.",
            
            "상품상태가 설명한 것과 같아요.",
            "나눔을 해주셨어요.",
            "상품설명이 자세해요.",
            "좋은 상품을 저렴하게 판매해요.",
            
            "제가 있는 곳까지 와서 거래했어요.",
    ]

    class Meta:
        model = User
        fields = (
            "manner",
        )
    
    def get_manner(self, user):
        reviewyee = user
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
        
        reviews = Review.objects.filter(reviewyee=reviewyee, manner_type="good").all()
        
        for review in reviews:
            manner = review.manner
            reviewer = review.reviewer
            for i, v in enumerate(manner):
                if v=="1":
                    good_manner_cnt[self.code_good_manner[i]].add(reviewer)
                    
        for manner in self.good_manner_list:
            good_manner_cnt[manner] = len(good_manner_cnt[manner])
            
        return good_manner_cnt
    
    
class UserReviewSerializer(serializers.ModelSerializer):
    review = serializers.SerializerMethodField()
    manner = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "review",
            "manner",
        )
        
    def get_review(self, user):
        reviewyee = user
        reviews = Review.objects.filter(Q(review_type="seller") | Q(review_type="buyer"), reviewyee=reviewyee)
        return ReviewSerializer(reviews, many=True).data
    
    def get_manner(self, user):
        return UserMannerSerializer(user).data