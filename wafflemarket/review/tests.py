from rest_framework import status

from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from factory.django import DjangoModelFactory

from review.models import Review, Temparature
from user.models import User
from user.serializers import jwt_token_of
from user.tests import UserFactory
from location.tests import LocationFactory
from article.tests import ArticleFactory

class TempFactory(DjangoModelFactory):
    class Meta:
        model = Temparature

    @classmethod
    def create(cls, **kwargs):
        temp = Temparature.objects.create(**kwargs)
        temp.save()
        return temp
    

class ReviewFactory(DjangoModelFactory):
    class Meta:
        model = Review

    @classmethod
    def create(cls, **kwargs):
        review = Review.objects.create(**kwargs)
        review.save()
        return review
    
class PostSellerReviewTestCase(TestCase):
    @classmethod
    def setUp(cls):
        cls.user1 = UserFactory(
            phone_number="01011112222",
            email="wafflemarket@test.com",
            username="steve",
        )
        cls.user1_token = "JWT " + jwt_token_of(
            User.objects.get(phone_number="01011112222")
        )
        cls.temp1 = TempFactory(
            user = cls.user1
        )

        cls.location1 = LocationFactory(
            code="1111011700",
            place_name="서울특별시 종로구 당주동",
        )
        cls.user1.location = cls.location1
        cls.user1.save()
        
        cls.user2 = UserFactory(
            phone_number="01022223333",
            username="mark",
        )
        cls.user2_token = "JWT " + jwt_token_of(
            User.objects.get(phone_number="01022223333")
        )
        cls.temp2 = TempFactory(
            user = cls.user2
        )

        cls.article1 = ArticleFactory(
            seller=cls.user1,
            location=cls.location1,
            price=3040000,
            title="맥북 판매",
            content="성능 좋은 맥북 판매해요.",
            category="디지털기기",
            sold_at = timezone.now(),
            buyer = cls.user2
        )
        
        cls.article2 = ArticleFactory(
            seller=cls.user1,
            location=cls.location1,
            price=10000,
            title="식물 판매",
            content="공기정화식물 판매해요.",
            category="식물",
        )
        
        cls.article3 = ArticleFactory(
            seller=cls.user2,
            location=cls.location1,
            price=40000,
            title="의자 판매",
            content="상태 아주 괜찮습니다. 1회 사용.",
            category="가구/인테리어",
            sold_at = timezone.now(),
            buyer = cls.user1
        )
        
        cls.post_data = {
            "review" : "거래 아주 만족합니다.",
            "manner_type" : "good",
            "manner_list" : [
                "친절하고 매너가 좋아요.",
                "상품설명이 자세해요."
            ]
        }
        
    def test_post_seller_review_no_login(self):
        pk = str(self.article1.id)
        
        # no token
        data = self.post_data.copy()
        response = self.client.post(
            "/api/v1/review/article/%s/seller/"%pk, 
            data=data,
            )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        review_count = Review.objects.count()
        self.assertEqual(review_count, 0)
        
    def test_post_seller_review_wrong_information(self):
        pk = str(self.article1.id)
        
        #wrong manner list (manner_type = good)
        data = self.post_data.copy()
        data["manner_list"] = ["친절하고 매너가 좋아요.", "반말을 사용해요."]
        response = self.client.post(
            "/api/v1/review/article/%s/seller/"%pk,
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user1_token,
            )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        #wrong manner list (manner_type = bad)
        data = self.post_data.copy()
        data["manner_type"] = "bad"
        data["manner_list"] = ["친절하고 매너가 좋아요.", "반말을 사용해요."]
        response = self.client.post(
            "/api/v1/review/article/%s/seller/"%pk,
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user1_token,
            )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        #wrong manner list (wrong)
        data = self.post_data.copy()
        data["manner_type"] = "good"
        data["manner_list"] = ["친절하고 매너가 좋아요"]
        response = self.client.post(
            "/api/v1/review/article/%s/seller/"%pk,
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user1_token,
            )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        #no manner list
        data = {
            "manner_type" : "good"
        }
        response = self.client.post(
            "/api/v1/review/article/%s/seller/"%pk,
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user1_token,
            )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        review_count = Review.objects.count()
        self.assertEqual(review_count, 0)
        
        
    def test_post_seller_review_wrong_id(self):
        # wrong pk
        wrong_pk = str(self.article1.id + 3)
        
        data = self.post_data.copy()
        response = self.client.post(
            "/api/v1/review/article/%s/seller/"%wrong_pk,
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user1_token,
            )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        res_data = response.json()
        self.assertEqual(res_data[0], "존재하지 않는 게시글입니다.")
        
        review_count = Review.objects.count()
        self.assertEqual(review_count, 0)
        
        
    def test_post_seller_review_not_sold(self):
        pk = str(self.article2.id)
        
        data = self.post_data.copy()
        response = self.client.post(
            "/api/v1/review/article/%s/seller/"%pk,
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user1_token,
            )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        res_data = response.json()
        self.assertEqual(res_data[0], "리뷰를 작성할 권한이 없습니다.")
        
        review_count = Review.objects.count()
        self.assertEqual(review_count, 0)
        
        
    def test_post_seller_review_not_seller(self):
        pk = str(self.article3.id)
        
        data = self.post_data.copy()
        response = self.client.post(
            "/api/v1/review/article/%s/seller/"%pk,
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user1_token,
            )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        res_data = response.json()
        self.assertEqual(res_data[0], "리뷰를 작성할 권한이 없습니다.")
        
        review_count = Review.objects.count()
        self.assertEqual(review_count, 0)
        
    def test_post_seller_review_success_no_review(self):
        pk = str(self.article1.id)
        
        # no review
        data = {
            "manner_type" : "good",
            "manner_list" : [
                "친절하고 매너가 좋아요.", 
                "상품설명이 자세해요."
                ]
        }
        response = self.client.post(
            "/api/v1/review/article/%s/seller/"%pk,
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user1_token,
            )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        res_data = response.json()
        self.assertEqual(res_data["review"], None)
        self.assertEqual(res_data["evaluation"], ["친절하고 매너가 좋아요.", "상품설명이 자세해요."])
        self.assertEqual(res_data["type"], "sent")
        to_view = res_data["to_view"]
        self.assertEqual(to_view[0], "received")
        self.assertEqual(to_view[1], False)
        
    def test_post_seller_review_success(self):
        pk = str(self.article1.id)
        data = self.post_data.copy()
        response = self.client.post(
            "/api/v1/review/article/%s/seller/"%pk,
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user1_token,
            )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        res_data = response.json()
        self.assertEqual(res_data["review"], "거래 아주 만족합니다.")
        self.assertEqual(res_data["evaluation"], ["친절하고 매너가 좋아요.", "상품설명이 자세해요."])
        self.assertEqual(res_data["type"], "sent")
        to_view = res_data["to_view"]
        self.assertEqual(to_view[0], "received")
        self.assertEqual(to_view[1], False)
        
        reviews = Review.objects.filter(article=self.article1, review_type="seller")
        self.assertEqual(reviews.count(), 1)
        review = Review.objects.get(article=self.article1, review_type="seller")
        self.assertEqual(review.review_type, "seller")
        self.assertEqual(review.review, "거래 아주 만족합니다.")
        self.assertEqual(review.review_location, self.location1)
        self.assertEqual(review.reviewer, self.user1)
        self.assertEqual(review.article, self.article1)
        self.assertEqual(review.reviewyee, self.user2)
        self.assertIsNotNone(review.created_at)
        self.assertEqual(review.manner_type, "good")
        self.assertEqual(review.manner, "10000100")
        
        response = self.client.post(
            "/api/v1/review/article/%s/seller/"%pk,
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user1_token,
            )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        res_data = response.json()
        self.assertEqual(res_data[0], "하나의 거래글 당 하나의 후기만 작성할 수 있습니다.")
        
        reviews = Review.objects.filter(article=self.article1, review_type="seller")
        self.assertEqual(reviews.count(), 1)
        
class PostBuyerReviewTestCase(TestCase):
    @classmethod
    def setUp(cls):
        cls.user1 = UserFactory(
            phone_number="01011112222",
            email="wafflemarket@test.com",
            username="steve",
        )
        cls.user1_token = "JWT " + jwt_token_of(
            User.objects.get(phone_number="01011112222")
        )
        cls.temp1 = TempFactory(
            user = cls.user1
        )
        
        cls.user2 = UserFactory(
            phone_number="01022223333",
            username="mark",
        )
        cls.user2_token = "JWT " + jwt_token_of(
            User.objects.get(phone_number="01022223333")
        )
        cls.temp2 = TempFactory(
            user = cls.user2
        )
        
        cls.location1 = LocationFactory(
            code="1111011700",
            place_name="서울특별시 종로구 당주동",
        )
        cls.user1.location = cls.location1
        cls.user1.save()
        cls.user2.location = cls.location1
        cls.user2.save()

        cls.article1 = ArticleFactory(
            seller=cls.user1,
            location=cls.location1,
            price=3040000,
            title="맥북 판매",
            content="성능 좋은 맥북 판매해요.",
            category="디지털기기",
            sold_at = timezone.now(),
            buyer = cls.user2
        )
        
        cls.article2 = ArticleFactory(
            seller=cls.user1,
            location=cls.location1,
            price=10000,
            title="식물 판매",
            content="공기정화식물 판매해요.",
            category="식물",
        )
        
        cls.article3 = ArticleFactory(
            seller=cls.user2,
            location=cls.location1,
            price=40000,
            title="의자 판매",
            content="상태 아주 괜찮습니다. 1회 사용.",
            category="가구/인테리어",
            sold_at = timezone.now(),
            buyer = cls.user1
        )
        
        cls.post_data = {
            "review" : "거래 아주 만족합니다.",
            "manner_type" : "good",
            "manner_list" : [
                "친절하고 매너가 좋아요.",
                "상품설명이 자세해요."
            ]
        }
        
    def test_post_buyer_review_no_login(self):
        pk = str(self.article1.id)
        
        # no token
        data = self.post_data.copy()
        response = self.client.post(
            "/api/v1/review/article/%s/buyer/"%pk, 
            data=data,
            )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        review_count = Review.objects.count()
        self.assertEqual(review_count, 0)
        
    def test_post_buyer_review_wrong_information(self):
        pk = str(self.article1.id)
        
        #wrong manner list (manner_type = good)
        data = self.post_data.copy()
        data["manner_list"] = ["친절하고 매너가 좋아요.", "반말을 사용해요."]
        response = self.client.post(
            "/api/v1/review/article/%s/buyer/"%pk,
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user2_token,
            )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        #wrong manner list (manner_type = bad)
        data = self.post_data.copy()
        data["manner_type"] = "bad"
        data["manner_list"] = ["친절하고 매너가 좋아요.", "반말을 사용해요."]
        response = self.client.post(
            "/api/v1/review/article/%s/buyer/"%pk,
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user2_token,
            )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        #wrong manner list (wrong)
        data = self.post_data.copy()
        data["manner_type"] = "good"
        data["manner_list"] = ["친절하고 매너가 좋아요"]
        response = self.client.post(
            "/api/v1/review/article/%s/buyer/"%pk,
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user2_token,
            )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        #no manner list
        data = {
            "manner_type" : "good"
        }
        response = self.client.post(
            "/api/v1/review/article/%s/buyer/"%pk,
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user2_token,
            )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        review_count = Review.objects.count()
        self.assertEqual(review_count, 0)
        
        
    def test_post_buyer_review_wrong_id(self):
        # wrong pk
        wrong_pk = str(self.article1.id + 3)
        
        data = self.post_data.copy()
        response = self.client.post(
            "/api/v1/review/article/%s/buyer/"%wrong_pk,
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user2_token,
            )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        res_data = response.json()
        self.assertEqual(res_data[0], "존재하지 않는 게시글입니다.")
        
        review_count = Review.objects.count()
        self.assertEqual(review_count, 0)
        
    def test_post_buyer_review_not_sold(self):
        pk = str(self.article2.id)
        
        data = self.post_data.copy()
        response = self.client.post(
            "/api/v1/review/article/%s/buyer/"%pk,
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user2_token,
            )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        res_data = response.json()
        self.assertEqual(res_data[0], "리뷰를 작성할 권한이 없습니다.")
        
        review_count = Review.objects.count()
        self.assertEqual(review_count, 0)
        
        
    def test_post_buyer_review_not_buyer(self):
        pk = str(self.article3.id)
        
        data = self.post_data.copy()
        response = self.client.post(
            "/api/v1/review/article/%s/buyer/"%pk,
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user2_token,
            )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        res_data = response.json()
        self.assertEqual(res_data[0], "리뷰를 작성할 권한이 없습니다.")
        
        review_count = Review.objects.count()
        self.assertEqual(review_count, 0)
        
    def test_post_buyer_review_success_no_review(self):
        pk = str(self.article1.id)
        
        # no review
        data = {
            "manner_type" : "good",
            "manner_list" : [
                "친절하고 매너가 좋아요.", 
                "상품설명이 자세해요."
                ]
        }
        response = self.client.post(
            "/api/v1/review/article/%s/buyer/"%pk,
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user2_token,
            )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        res_data = response.json()
        self.assertEqual(res_data["review"], None)
        self.assertEqual(res_data["evaluation"], ["친절하고 매너가 좋아요.", "상품설명이 자세해요."])
        self.assertEqual(res_data["type"], "sent")
        to_view = res_data["to_view"]
        self.assertEqual(to_view[0], "received")
        self.assertEqual(to_view[1], False)
        
    def test_post_buyer_review_success(self):
        pk = str(self.article1.id)
        data = self.post_data.copy()
        response = self.client.post(
            "/api/v1/review/article/%s/buyer/"%pk,
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user2_token,
            )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        res_data = response.json()
        self.assertEqual(res_data["review"], "거래 아주 만족합니다.")
        self.assertEqual(res_data["evaluation"], ["친절하고 매너가 좋아요.", "상품설명이 자세해요."])
        self.assertEqual(res_data["type"], "sent")
        to_view = res_data["to_view"]
        self.assertEqual(to_view[0], "received")
        self.assertEqual(to_view[1], False)
        
        reviews = Review.objects.filter(article=self.article1, review_type="buyer")
        self.assertEqual(reviews.count(), 1)
        review = Review.objects.get(article=self.article1, review_type="buyer")
        self.assertEqual(review.review_type, "buyer")
        self.assertEqual(review.review, "거래 아주 만족합니다.")
        self.assertEqual(review.review_location, self.location1)
        self.assertEqual(review.reviewer, self.user2)
        self.assertEqual(review.article, self.article1)
        self.assertEqual(review.reviewyee, self.user1)
        self.assertIsNotNone(review.created_at)
        self.assertEqual(review.manner_type, "good")
        self.assertEqual(review.manner, "10000100")
        
        response = self.client.post(
            "/api/v1/review/article/%s/buyer/"%pk,
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user2_token,
            )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        res_data = response.json()
        self.assertEqual(res_data[0], "하나의 거래글 당 하나의 후기만 작성할 수 있습니다.")
        
        reviews = Review.objects.filter(article=self.article1, review_type="buyer")
        self.assertEqual(reviews.count(), 1)

class GetSentReviewTestCase(TestCase):
    @classmethod
    def setUp(cls):
        cls.user1 = UserFactory(
            phone_number="01011112222",
            email="wafflemarket@test.com",
            username="steve",
        )
        cls.user1_token = "JWT " + jwt_token_of(
            User.objects.get(phone_number="01011112222")
        )
        cls.temp1 = TempFactory(
            user = cls.user1
        )

        cls.location1 = LocationFactory(
            code="1111011700",
            place_name="서울특별시 종로구 당주동",
        )
        cls.user1.location = cls.location1
        cls.user1.save()
        
        cls.user2 = UserFactory(
            phone_number="01022223333",
            username="mark",
        )
        cls.user2_token = "JWT " + jwt_token_of(
            User.objects.get(phone_number="01022223333")
        )
        cls.temp2 = TempFactory(
            user = cls.user2
        )
        
        cls.user3 = UserFactory(
            phone_number="01033334444",
            username="smith",
        )
        cls.user3_token = "JWT " + jwt_token_of(
            User.objects.get(phone_number="01033334444")
        )

        cls.article1 = ArticleFactory(
            seller=cls.user1,
            location=cls.location1,
            price=3040000,
            title="맥북 판매",
            content="성능 좋은 맥북 판매해요.",
            category="디지털기기",
            sold_at=timezone.now(),
            buyer=cls.user2
        )
        
        cls.article2 = ArticleFactory(
            seller=cls.user1,
            location=cls.location1,
            price=10000,
            title="식물 판매",
            content="공기정화식물 판매해요.",
            category="식물",
            sold_at=timezone.now(),
            buyer=cls.user1
        )
        
        cls.article3 = ArticleFactory(
            seller=cls.user2,
            location=cls.location1,
            price=40000,
            title="의자 판매",
            content="상태 아주 괜찮습니다. 1회 사용.",
            category="가구/인테리어",
            sold_at = timezone.now(),
            buyer = cls.user1
        )
        
        cls.review1 = ReviewFactory(
            review_type="seller",
            reviewer = cls.user1,
            article = cls.article1,
            review_location = cls.location1,
            reviewyee = cls.user2,
            review="거래 매우 불만족합니다.",
            manner_type="bad",
            manner="1111100000000000"
        )
        
        cls.review2 = ReviewFactory(
            review_type="buyer",
            reviewer = cls.user1,
            article = cls.article2,
            review_location = cls.location1,
            reviewyee = cls.user2,
            review="거래 매우 만족합니다.",
            manner_type="good",
            manner="11000000"
        )
        
        cls.review3 = ReviewFactory(
            review_type="buyer",
            reviewer = cls.user2,
            article = cls.article1,
            review_location = cls.location1,
            reviewyee = cls.user1,
            review="거래 매우 만족합니다.",
            manner_type="good",
            manner="11000000"
        )
        
    def test_get_sent_review_no_login(self):
        pk = str(self.article1.id)
        
        # no token
        response = self.client.get(
            "/api/v1/review/article/%s/sent/"%pk,
            data={},
            )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_get_sent_review_wrong_article(self):
        pk = str(self.article1.id + 3)
        
        # wrong article
        response = self.client.get(
            "/api/v1/review/article/%s/sent/"%pk,
            data={},
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user2_token,
            )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        res_data = response.json()
        self.assertEqual(res_data[0], "존재하지 않는 게시글입니다.")
        
    def test_get_sent_review_not_seller_or_buyer(self):
        pk = str(self.article1.id)
        
        # not seller or buyer
        response = self.client.get(
            "/api/v1/review/article/%s/sent/"%pk,
            data={},
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user3_token,
            )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        res_data = response.json()
        self.assertEqual(res_data[0], "해당 게시글의 판매자 혹은 구매자만이 후기를 조회 혹은 삭제할 수 있습니다.")
       
        
    def test_get_sent_review_none(self):
        pk = str(self.article3.id)
        
        # no review sent
        response = self.client.get(
            "/api/v1/review/article/%s/sent/"%pk,
            data={},
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user1_token,
            )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        res_data = response.json()
        self.assertEqual(res_data[0], "후기가 존재하지 않습니다.")
     
        
    def test_get_sent_review_seller_success(self):
        pk = str(self.article1.id)
        
        response = self.client.get(
            "/api/v1/review/article/%s/sent/"%pk,
            data={},
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user1_token,
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        res_data = response.json()
        self.assertEqual(res_data["review"], "거래 매우 불만족합니다.")
        self.assertEqual(res_data["evaluation"], 
                            [
                                "반말을 사용해요.", 
                                "불친절해요.", 
                                "무조건 택배거래만 하려고 해요.", 
                                "채팅 메시지를 보내도 답이 없어요.", 
                                "차에서 내리지도 않고 창문만 열고 거래하려고 해요."
                            ]
                        )
        self.assertEqual(res_data["type"], "sent")
        to_view = res_data["to_view"]
        self.assertEqual(to_view[0], "received")
        self.assertEqual(to_view[1], True)
        
        
    def test_get_sent_review_buyer_success(self):
        pk = str(self.article2.id)
        
        response = self.client.get(
            "/api/v1/review/article/%s/sent/"%pk,
            data={},
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user1_token,
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        res_data = response.json()
        self.assertEqual(res_data["review"], "거래 매우 만족합니다.")
        self.assertEqual(res_data["evaluation"], ["친절하고 매너가 좋아요.", "시간 약속을 잘 지켜요."])
        self.assertEqual(res_data["type"], "sent")
        to_view = res_data["to_view"]
        self.assertEqual(to_view[0], "received")
        self.assertEqual(to_view[1], False)
        
        
class DeleteSentReviewTestCase(TestCase):
    @classmethod
    def setUp(cls):
        cls.user1 = UserFactory(
            phone_number="01011112222",
            email="wafflemarket@test.com",
            username="steve",
        )
        cls.user1_token = "JWT " + jwt_token_of(
            User.objects.get(phone_number="01011112222")
        )
        cls.temp1 = TempFactory(
            user = cls.user1
        )

        cls.location1 = LocationFactory(
            code="1111011700",
            place_name="서울특별시 종로구 당주동",
        )
        cls.user1.location = cls.location1
        cls.user1.save()
        
        cls.user2 = UserFactory(
            phone_number="01022223333",
            username="mark",
        )
        cls.user2_token = "JWT " + jwt_token_of(
            User.objects.get(phone_number="01022223333")
        )
        cls.temp2 = TempFactory(
            user = cls.user2
        )
        
        cls.user3 = UserFactory(
            phone_number="01033334444",
            username="smith",
        )
        cls.user3_token = "JWT " + jwt_token_of(
            User.objects.get(phone_number="01033334444")
        )

        cls.article1 = ArticleFactory(
            seller=cls.user1,
            location=cls.location1,
            price=3040000,
            title="맥북 판매",
            content="성능 좋은 맥북 판매해요.",
            category="디지털기기",
            sold_at=timezone.now(),
            buyer=cls.user2
        )
        
        cls.article2 = ArticleFactory(
            seller=cls.user1,
            location=cls.location1,
            price=10000,
            title="식물 판매",
            content="공기정화식물 판매해요.",
            category="식물",
            sold_at=timezone.now(),
            buyer=cls.user1
        )
        
        cls.article3 = ArticleFactory(
            seller=cls.user2,
            location=cls.location1,
            price=40000,
            title="의자 판매",
            content="상태 아주 괜찮습니다. 1회 사용.",
            category="가구/인테리어",
            sold_at = timezone.now(),
            buyer = cls.user1
        )
        
        cls.review1 = ReviewFactory(
            review_type="seller",
            reviewer = cls.user1,
            article = cls.article1,
            review_location = cls.location1,
            reviewyee = cls.user2,
            review="거래 매우 불만족합니다.",
            manner_type="bad",
            manner="1111100000000000"
        )
        
        cls.review2 = ReviewFactory(
            review_type="buyer",
            reviewer = cls.user1,
            article = cls.article2,
            review_location = cls.location1,
            reviewyee = cls.user2,
            review="거래 매우 만족합니다.",
            manner_type="good",
            manner="11000000"
        )
        
        cls.review3 = ReviewFactory(
            review_type="buyer",
            reviewer = cls.user2,
            article = cls.article1,
            review_location = cls.location1,
            reviewyee = cls.user1,
            review="거래 매우 만족합니다.",
            manner_type="good",
            manner="11000000"
        )
        
    def test_delete_sent_review_no_login(self):
        pk = str(self.article1.id)
        
        # no token
        response = self.client.delete(
            "/api/v1/review/article/%s/sent/"%pk,
            data={},
            )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        reviews = Review.objects.all()
        self.assertEqual(reviews.count(), 3)

        
    def test_delete_sent_review_wrong_article(self):
        pk = str(self.article1.id + 3)
        
        # wrong article
        response = self.client.delete(
            "/api/v1/review/article/%s/sent/"%pk,
            data={},
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user2_token,
            )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        res_data = response.json()
        self.assertEqual(res_data[0], "존재하지 않는 게시글입니다.")
        
        reviews = Review.objects.all()
        self.assertEqual(reviews.count(), 3)
        
    def test_delete_sent_review_not_seller_or_buyer(self):
        pk = str(self.article1.id)
        
        # not seller or buyer
        response = self.client.delete(
            "/api/v1/review/article/%s/sent/"%pk,
            data={},
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user3_token,
            )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        res_data = response.json()
        self.assertEqual(res_data[0], "해당 게시글의 판매자 혹은 구매자만이 후기를 조회 혹은 삭제할 수 있습니다.")
        
        reviews = Review.objects.all()
        self.assertEqual(reviews.count(), 3)
       
        
    def test_delete_sent_review_none(self):
        pk = str(self.article3.id)
        
        # no review sent
        response = self.client.delete(
            "/api/v1/review/article/%s/sent/"%pk,
            data={},
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user1_token,
            )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        res_data = response.json()
        self.assertEqual(res_data[0], "후기가 존재하지 않습니다.")
        
        reviews = Review.objects.all()
        self.assertEqual(reviews.count(), 3)
     
        
    def test_delete_sent_review_seller_success(self):
        pk = str(self.article1.id)
        
        response = self.client.delete(
            "/api/v1/review/article/%s/sent/"%pk,
            data={},
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user1_token,
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        reviews = Review.objects.all()
        self.assertEqual(reviews.count(), 2)
        
        
    def test_delete_sent_review_buyer_success(self):
        pk = str(self.article1.id)
        
        response = self.client.delete(
            "/api/v1/review/article/%s/sent/"%pk,
            data={},
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user2_token,
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        reviews = Review.objects.all()
        self.assertEqual(reviews.count(), 2)
        
        
class GetReceivedReviewTestCase(TestCase):
    @classmethod
    def setUp(cls):
        cls.user1 = UserFactory(
            phone_number="01011112222",
            email="wafflemarket@test.com",
            username="steve",
        )
        cls.user1_token = "JWT " + jwt_token_of(
            User.objects.get(phone_number="01011112222")
        )
        cls.temp1 = TempFactory(
            user = cls.user1
        )

        cls.location1 = LocationFactory(
            code="1111011700",
            place_name="서울특별시 종로구 당주동",
        )
        cls.user1.location = cls.location1
        cls.user1.save()
        
        cls.user2 = UserFactory(
            phone_number="01022223333",
            username="mark",
        )
        cls.user2_token = "JWT " + jwt_token_of(
            User.objects.get(phone_number="01022223333")
        )
        cls.temp2 = TempFactory(
            user = cls.user2
        )
        
        cls.user3 = UserFactory(
            phone_number="01033334444",
            username="smith",
        )
        cls.user3_token = "JWT " + jwt_token_of(
            User.objects.get(phone_number="01033334444")
        )
        cls.temp3 = TempFactory(
            user = cls.user3
        )

        cls.article1 = ArticleFactory(
            seller=cls.user1,
            location=cls.location1,
            price=3040000,
            title="맥북 판매",
            content="성능 좋은 맥북 판매해요.",
            category="디지털기기",
            sold_at=timezone.now(),
            buyer=cls.user2
        )
        
        cls.article2 = ArticleFactory(
            seller=cls.user1,
            location=cls.location1,
            price=10000,
            title="식물 판매",
            content="공기정화식물 판매해요.",
            category="식물",
            sold_at=timezone.now(),
            buyer=cls.user2
        )
        
        cls.article3 = ArticleFactory(
            seller=cls.user2,
            location=cls.location1,
            price=40000,
            title="의자 판매",
            content="상태 아주 괜찮습니다. 1회 사용.",
            category="가구/인테리어",
            sold_at = timezone.now(),
            buyer = cls.user1
        )
        
        cls.review1 = ReviewFactory(
            review_type="seller",
            reviewer = cls.user1,
            article = cls.article1,
            review_location = cls.location1,
            reviewyee = cls.user2,
            review="거래 매우 불만족합니다.",
            manner_type="bad",
            manner="1111100000000000"
        )
        
        cls.review2 = ReviewFactory(
            review_type="buyer",
            reviewer = cls.user1,
            article = cls.article2,
            review_location = cls.location1,
            reviewyee = cls.user2,
            review="거래 매우 만족합니다.",
            manner_type="good",
            manner="11000000"
        )
        
        cls.review3 = ReviewFactory(
            review_type="buyer",
            reviewer = cls.user2,
            article = cls.article1,
            review_location = cls.location1,
            reviewyee = cls.user1,
            review="거래 매우 만족합니다.",
            manner_type="good",
            manner="11000000"
        )
        
    def test_get_received_review_no_login(self):
        pk = str(self.article1.id)
        
        # no token
        response = self.client.get(
            "/api/v1/review/article/%s/received/"%pk,
            data={},
            )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_get_received_review_wrong_article(self):
        pk = str(self.article1.id + 3)
        
        # wrong article
        response = self.client.get(
            "/api/v1/review/article/%s/received/"%pk,
            data={},
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user2_token,
            )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        res_data = response.json()
        self.assertEqual(res_data[0], "존재하지 않는 게시글입니다.")
        
    def test_get_received_review_not_seller_or_buyer(self):
        pk = str(self.article1.id)
        
        # not seller or buyer
        response = self.client.get(
            "/api/v1/review/article/%s/received/"%pk,
            data={},
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user3_token,
            )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        res_data = response.json()
        self.assertEqual(res_data[0], "해당 게시글의 판매자 혹은 구매자만이 후기를 조회할 수 있습니다.")
       
        
    def test_get_received_review_none(self):
        pk = str(self.article3.id)
        
        # no review sent
        response = self.client.get(
            "/api/v1/review/article/%s/received/"%pk,
            data={},
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user1_token,
            )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        res_data = response.json()
        self.assertEqual(res_data[0], "후기가 존재하지 않습니다.")
     
        
    def test_get_received_review_seller_success(self):
        pk = str(self.article1.id)
        
        response = self.client.get(
            "/api/v1/review/article/%s/received/"%pk,
            data={},
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user1_token,
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        res_data = response.json()
        self.assertEqual(res_data["review"], "거래 매우 만족합니다.")
        self.assertEqual(res_data["evaluation"], ["친절하고 매너가 좋아요.", "시간 약속을 잘 지켜요."])
        self.assertEqual(res_data["type"], "received")
        to_view = res_data["to_view"]
        self.assertEqual(to_view[0], "sent")
        self.assertEqual(to_view[1], True)
        
        
    def test_get_received_review_buyer_success(self):
        pk = str(self.article1.id)
        
        response = self.client.get(
            "/api/v1/review/article/%s/received/"%pk,
            data={},
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user2_token,
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        res_data = response.json()
        self.assertEqual(res_data["review"], "거래 매우 불만족합니다.")
        self.assertEqual(res_data["evaluation"], 
                            [
                                "반말을 사용해요.", 
                                "불친절해요.", 
                                "무조건 택배거래만 하려고 해요.", 
                                "채팅 메시지를 보내도 답이 없어요.", 
                                "차에서 내리지도 않고 창문만 열고 거래하려고 해요."
                            ]
                        )
        self.assertEqual(res_data["type"], "received")
        to_view = res_data["to_view"]
        self.assertEqual(to_view[0], "sent")
        self.assertEqual(to_view[1], True)

        
class PutUserReviewTestCase(TestCase):
    @classmethod
    def setUp(cls):

        cls.user1 = UserFactory(
            phone_number="01011112222",
            email="wafflemarket@test.com",
            username="steve",
        )
        cls.user1_token = "JWT " + jwt_token_of(
            User.objects.get(phone_number="01011112222")
        )

        cls.location1 = LocationFactory(
            code="1111011700",
            place_name="서울특별시 종로구 당주동",
        )
        cls.user1.location = cls.location1
        cls.user1.save()
        
        cls.user2 = UserFactory(
            phone_number="01022223333",
            username="mark",
        )
        cls.user2_token = "JWT " + jwt_token_of(
            User.objects.get(phone_number="01022223333")
        )

        cls.user1.location = cls.location1
        cls.user1.save()
        
        cls.put_data = {
            "manner_list" : [
                "친절하고 매너가 좋아요.",
                "시간 약속을 잘 지켜요."
            ]
        }
        
    def test_put_user_review_no_login(self):
        pk = str(self.user1.id)
        
        # no token
        data = self.put_data.copy()
        response = self.client.put(
            "/api/v1/review/user/%s/manner/good/"%pk, 
            data=data,
            )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        review_count = Review.objects.count()
        self.assertEqual(review_count, 0)
        
    def test_put_user_review_wrong_information(self):
        pk = str(self.user1.id)
        
        #wrong manner list (manner_type = good)
        data = self.put_data.copy()
        data["manner_list"] = ["친절하고 매너가 좋아요.", "반말을 사용해요."]
        response = self.client.put(
            "/api/v1/review/user/%s/manner/good/"%pk,
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user2_token,
            )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        #wrong manner list (manner_type = bad)
        data = self.put_data.copy()
        data["manner_list"] = ["친절하고 매너가 좋아요.", "반말을 사용해요."]
        response = self.client.put(
            "/api/v1/review/user/%s/manner/bad/"%pk,
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user2_token,
            )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        #wrong manner list (wrong)
        data = self.put_data.copy()
        data["manner_list"] = ["친절하고 매너가 좋아요"]
        response = self.client.put(
            "/api/v1/review/user/%s/manner/good/"%pk,
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user2_token,
            )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        #no manner list
        response = self.client.put(
            "/api/v1/review/user/%s/manner/good/"%pk,
            data={},
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user2_token,
            )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        review_count = Review.objects.count()
        self.assertEqual(review_count, 0)
        
        
    def test_put_user_review_wrong_id(self):
        # wrong pk
        wrong_pk = str(self.user1.id + 3)
        
        data = self.put_data.copy()
        response = self.client.put(
            "/api/v1/review/user/%s/manner/good/"%wrong_pk,
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user2_token,
            )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        res_data = response.json()
        self.assertEqual(res_data[0], "존재하지 않는 사용자입니다.")
        
        review_count = Review.objects.count()
        self.assertEqual(review_count, 0)
        
        
    def test_put_user_review_success(self):
        pk = str(self.user1.id)
        
        # first put
        
        data = self.put_data.copy()
        response = self.client.put(
            "/api/v1/review/user/%s/manner/good/"%pk,
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user2_token,
            )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        res_data = response.json()
        self.assertEqual(res_data["manner_type"], "good")
        self.assertEqual(res_data["evaluation"], ["친절하고 매너가 좋아요.", "시간 약속을 잘 지켜요."])
        
        reviews = Review.objects.filter(reviewyee=self.user1, reviewer=self.user2, review_type="user")
        self.assertEqual(reviews.count(), 1)
        review = Review.objects.get(reviewyee=self.user1, reviewer=self.user2, review_type="user")
        self.assertEqual(review.review_type, "user")
        self.assertIsNone(review.review)
        self.assertEqual(review.reviewyee, self.user1)
        self.assertEqual(review.reviewer, self.user2)
        self.assertIsNotNone(review.created_at)
        self.assertEqual(review.manner_type, "good")
        self.assertEqual(review.manner, "110")
        
        # not first put
        data = {
            "manner_list" : [
                "친절하고 매너가 좋아요."
            ]
        }
        
        response = self.client.put(
            "/api/v1/review/user/%s/manner/good/"%pk,
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user2_token,
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        res_data = response.json()
        self.assertEqual(res_data["manner_type"], "good")
        self.assertEqual(res_data["evaluation"], ["친절하고 매너가 좋아요."])
        
        reviews = Review.objects.filter(reviewyee=self.user1, reviewer=self.user2, review_type="user")
        self.assertEqual(reviews.count(), 1)
        review = Review.objects.get(reviewyee=self.user1, reviewer=self.user2, review_type="user")
        self.assertEqual(review.review_type, "user")
        self.assertIsNone(review.review)
        self.assertIsNone(review.review_location)
        self.assertEqual(review.reviewyee, self.user1)
        self.assertEqual(review.reviewer, self.user2)
        self.assertIsNotNone(review.created_at)
        self.assertEqual(review.manner_type, "good")
        self.assertEqual(review.manner, "100")
        

class GetUserReviewTestCase(TestCase):
    @classmethod
    def setUp(cls):
        cls.user1 = UserFactory(
            phone_number="01011112222",
            email="wafflemarket@test.com",
            username="steve",
        )
        cls.user1_token = "JWT " + jwt_token_of(
            User.objects.get(phone_number="01011112222")
        )
        cls.temp1 = TempFactory(
            user = cls.user1
        )

        cls.location1 = LocationFactory(
            code="1111011700",
            place_name="서울특별시 종로구 당주동",
        )
        cls.user1.location = cls.location1
        cls.user1.save()
        
        cls.user2 = UserFactory(
            phone_number="01022223333",
            username="mark",
        )
        cls.user2_token = "JWT " + jwt_token_of(
            User.objects.get(phone_number="01022223333")
        )
        cls.temp2 = TempFactory(
            user = cls.user2
        )
        
    def test_get_user_review_no_login(self):
        pk = str(self.user1.id)
        
        # no token
        response = self.client.get(
            "/api/v1/review/user/%s/manner/good/"%pk, 
            data={},
            )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_get_user_review_wrong_id(self):
        # wrong pk
        wrong_pk = str(self.user1.id + 3)
        
        response = self.client.get(
            "/api/v1/review/user/%s/manner/good/"%wrong_pk,
            data={},
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user2_token,
            )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        res_data = response.json()
        self.assertEqual(res_data[0], "존재하지 않는 사용자입니다.")
        
        review_count = Review.objects.count()
        self.assertEqual(review_count, 0)
        
    def test_get_user_review_success(self):
        pk = str(self.user1.id)
        
        # first get
        response = self.client.get(
            "/api/v1/review/user/%s/manner/good/"%pk,
            data={},
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user2_token,
            )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        res_data = response.json()
        self.assertEqual(res_data["manner_type"], "good")
        self.assertEqual(res_data["evaluation"], [])
        
        #not first get
        review = ReviewFactory(
            reviewer = self.user1,
            reviewyee = self.user2,
            review_type = "user",
            article=None, 
            review = None,
            review_location = None,
            manner_type = type,
            manner = "11000000"
        )
        
        response = self.client.get(
            "/api/v1/review/user/%s/manner/good/"%pk,
            data={},
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user1_token,
            )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        res_data = response.json()
        self.assertEqual(res_data["manner_type"], "good")
        self.assertEqual(res_data["evaluation"], ["친절하고 매너가 좋아요.", "시간 약속을 잘 지켜요."])



class GetUserReviewTestCase(TestCase):
    @classmethod
    def setUp(cls):
        cls.user1 = UserFactory(
            phone_number="01011112222",
            email="wafflemarket@test.com",
            username="steve",
        )
        cls.user1_token = "JWT " + jwt_token_of(
            User.objects.get(phone_number="01011112222")
        )
        cls.temp1 = TempFactory(
            user = cls.user1
        )

        cls.location1 = LocationFactory(
            code="1111011700",
            place_name="서울특별시 종로구 당주동",
        )
        cls.user1.location = cls.location1
        cls.user1.save()
        
        cls.user2 = UserFactory(
            phone_number="01022223333",
            username="mark",
        )
        cls.user2_token = "JWT " + jwt_token_of(
            User.objects.get(phone_number="01022223333")
        )
        cls.temp2 = TempFactory(
            user = cls.user2
        )
        
        cls.user3 = UserFactory(
            phone_number="01033334444",
            username="smith",
        )
        cls.user3_token = "JWT " + jwt_token_of(
            User.objects.get(phone_number="01033334444")
        )
        cls.temp3 = TempFactory(
            user = cls.user3
        )

        cls.article1 = ArticleFactory(
            seller=cls.user1,
            location=cls.location1,
            price=3040000,
            title="맥북 판매",
            content="성능 좋은 맥북 판매해요.",
            category="디지털기기",
            sold_at=timezone.now(),
            buyer=cls.user2
        )
        
        cls.article2 = ArticleFactory(
            seller=cls.user2,
            location=cls.location1,
            price=10000,
            title="식물 판매",
            content="공기정화식물 판매해요.",
            category="식물",
            sold_at=timezone.now(),
            buyer=cls.user1
        )
        
        cls.review1 = ReviewFactory(
            review_type = "seller",
            reviewer = cls.user1,
            article = cls.article1,
            review_location = cls.location1,
            reviewyee = cls.user2,
            review="거래 매우 불만족합니다.",
            manner_type = "bad",
            manner = "1111100000000000"
        )
        
        cls.review2 = ReviewFactory(
            review_type="seller",
            reviewer = cls.user1,
            article = cls.article1,
            review_location = cls.location1,
            reviewyee = cls.user3,
            review="거래 매우 만족합니다.",
            manner_type="good",
            manner="11000000"
        )
        
        cls.review3 = ReviewFactory(
            review_type="buyer",
            reviewer = cls.user2,
            article = cls.article1,
            review_location = cls.location1,
            reviewyee = cls.user1,
            review="거래 매우 만족합니다.",
            manner_type="good",
            manner="11000000"
        )
        
        cls.review4 = ReviewFactory(
            review_type="user",
            reviewer = cls.user2,
            article = cls.article1,
            review_location = cls.location1,
            reviewyee = cls.user1,
            review="거래 매우 만족합니다.",
            manner_type="good",
            manner="11000000"
        )
        
        cls.review4 = ReviewFactory(
            review_type="user",
            reviewer = cls.user3,
            article = cls.article1,
            review_location = cls.location1,
            reviewyee = cls.user1,
            review="거래 매우 불만족합니다.",
            manner_type="bad",
            manner="1111100000000000"
        )
        
    def test_get_user_review_no_login(self):
        pk = str(self.user1.id)
        
        # no token
        response = self.client.get(
            "/api/v1/review/user/%s/"%pk,
            data={},
            )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        
        response = self.client.get(
            "/api/v1/review/user/%s/review/"%pk,
            data={},
            )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        
        response = self.client.get(
            "/api/v1/review/user/%s/manner/"%pk,
            data={},
            )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        
    def test_get_user_review_wrong_id(self):
        # wrong pk
        wrong_pk = str(self.user1.id + 3)
        
        response = self.client.get(
            "/api/v1/review/user/%s/"%wrong_pk,
            data={},
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user1_token,
            )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        res_data = response.json()
        self.assertEqual(res_data[0], "존재하지 않는 사용자입니다.")
        
        
        response = self.client.get(
            "/api/v1/review/user/%s/manner/"%wrong_pk,
            data={},
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user1_token,
            )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        res_data = response.json()
        self.assertEqual(res_data[0], "존재하지 않는 사용자입니다.")
        
        
        response = self.client.get(
            "/api/v1/review/user/%s/review/"%wrong_pk,
            data={},
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user1_token,
            )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        res_data = response.json()
        self.assertEqual(res_data[0], "존재하지 않는 사용자입니다.")
        
    
    def test_get_review_success(self):
        pk = str(self.user1.id)
        
        response = self.client.get(
            "/api/v1/review/user/%s/"%pk,
            data={},
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user1_token,
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_get_review_review_success(self):
        pk = str(self.user1.id)
        
        response = self.client.get(
            "/api/v1/review/user/%s/manner/"%pk,
            data={},
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user1_token,
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_get_review_manner_success(self):
        pk = str(self.user1.id)
        
        response = self.client.get(
            "/api/v1/review/user/%s/review/"%pk,
            data={},
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user1_token,
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
