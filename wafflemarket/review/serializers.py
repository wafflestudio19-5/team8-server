from rest_framework import serializers

from review.models import Review
from location.models import Location

class ReviewArticleValidator(serializers.Serializer):
    review = serializers.CharField()
    manner_type = serializers.CharField()
    manner_list = serializers.ListField(child=serializers.CharField())
    
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
        review = data.get("review")
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