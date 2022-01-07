from rest_framework import status
from django.test import TestCase, TransactionTestCase
from factory.django import DjangoModelFactory

from user.models import User
from user.serializers import jwt_token_of


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    @classmethod
    def create(cls, **kwargs):
        user = User.objects.create(**kwargs)
        user.set_password(kwargs.get("password", ""))
        user.save()
        return user


class PostUserTestCase(TransactionTestCase):
    @classmethod
    def setUp(cls):

        cls.user = UserFactory(
            phone_number="01011112222",
            username="steve",
        )

        cls.post_data = {
            "phone_number": "01022223333",
            "username": "mark",
        }

    def test_post_user_wrong_information(self):
        # no phone_number
        data = self.post_data.copy()
        data.pop("phone_number")
        response = self.client.post("/api/v1/signup/", data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        res_data = response.json()
        self.assertEqual(res_data["phone_number"], ["This field is required."])

        user_count = User.objects.count()
        self.assertEqual(user_count, 1)

        # invalid phone_number
        data = self.post_data.copy()
        data["phone_number"] = "010-1111-2222"
        response = self.client.post("/api/v1/signup/", data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        res_data = response.json()
        self.assertEqual(res_data["non_field_errors"], ["전화번호가 올바르지 않아요."])

        user_count = User.objects.count()
        self.assertEqual(user_count, 1)

        # no username
        data = self.post_data.copy()
        data.pop("username")
        response = self.client.post("/api/v1/signup/", data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        res_data = response.json()
        self.assertEqual(res_data["username"], ["This field is required."])

        user_count = User.objects.count()
        self.assertEqual(user_count, 1)

        # invalid username
        data = self.post_data.copy()
        data["username"] = "waffle!"
        response = self.client.post("/api/v1/signup/", data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        res_data = response.json()
        self.assertEqual(res_data["non_field_errors"], ["닉네임은 띄어쓰기 없이 영문 한글 숫자만 가능해요."])

        user_count = User.objects.count()
        self.assertEqual(user_count, 1)

    def test_post_user_duplicate(self):
        # same phone_number(=login)
        data = self.post_data.copy()
        data.update({"phone_number": "01011112222"})
        response = self.client.post("/api/v1/signup/", data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        res_data = response.json()
        self.assertEqual(res_data["phone_number"], "01011112222")
        self.assertEqual(res_data["username"], "steve")
        self.assertEqual(res_data["logined"], True)
        self.assertEqual(res_data["first_login"], True)
        self.assertEqual(res_data["location_exists"], False)
        self.assertIn("token", res_data)

        user_count = User.objects.count()
        self.assertEqual(user_count, 1)

    def test_post_user_sucess(self):
        # successively register user
        data = self.post_data.copy()
        response = self.client.post("/api/v1/signup/", data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        res_data = response.json()
        self.assertEqual(res_data["phone_number"], "01022223333")
        self.assertEqual(res_data["username"], "mark")
        self.assertEqual(res_data["logined"], True)
        self.assertEqual(res_data["first_login"], True)
        self.assertEqual(res_data["location_exists"], False)
        self.assertIn("token", res_data)

        user_count = User.objects.count()
        self.assertEqual(user_count, 2)
        user = User.objects.get(phone_number="01022223333")
        self.assertEqual(user.username, "mark")
        self.assertIsNone(user.location)
        self.assertIsNotNone(user.created_at)
        self.assertIsNotNone(user.last_login)
        self.assertTrue(user.is_active)


class PutUserCategoryTestCase(TestCase):
    @classmethod
    def setUp(cls):
        cls.user = UserFactory(
            phone_number="01033334444",
            email="wafflemarket@test.com",
            username="steve",
        )
        cls.user_token = "JWT " + jwt_token_of(User.objects.get(phone_number="01033334444"))
        cls.put_data = {
            "category": "디지털기기",
            "enabled": "False",
        }

    def test_put_category_no_login(self):
        # no token
        data = self.put_data.copy()
        response = self.client.put(
            "/api/v1/user/category/", data=data, content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        user = User.objects.get(phone_number="01033334444")
        self.assertEqual(user.interest, "1" * 17)

    def test_put_category_wrong_information(self):
        # invalid category
        data = self.put_data.copy()
        data["category"] = "invalid"
        response = self.client.put(
            "/api/v1/user/category/",
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["non_field_errors"][0], "카테고리가 부적절해요.")
        user = User.objects.get(phone_number="01033334444")
        self.assertEqual(user.interest, "1" * 17)

        # invalid enabled
        data = self.put_data.copy()
        data["enabled"] = "invalid"
        response = self.client.put(
            "/api/v1/user/category/",
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["enabled"][0], "Must be a valid boolean.")
        user = User.objects.get(phone_number="01033334444")
        self.assertEqual(user.interest, "1" * 17)

    def test_put_category_success(self):

        # successfully change enabled 'true' to 'false'
        data = self.put_data.copy()
        response = self.client.put(
            "/api/v1/user/category/",
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("디지털기기", response.json()["category"])
        self.assertIn("가구/인테리어", response.json()["category"])
        user = User.objects.get(phone_number="01033334444")
        self.assertEqual(user.interest, "0" + "1" * 16)

        response = self.client.put(
            "/api/v1/user/category/",
            data={"category": "가구/인테리어", "enabled": "FALSE"},
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("디지털기기", response.json()["category"])
        self.assertNotIn("가구/인테리어", response.json()["category"])
        user = User.objects.get(phone_number="01033334444")
        self.assertEqual(user.interest, "00" + "1" * 15)

        # successfully change enabled 'true' to 'false'
        data = self.put_data.copy()
        data["enabled"] = "True"
        response = self.client.put(
            "/api/v1/user/category/",
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=self.user_token,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("디지털기기", response.json()["category"])
        self.assertNotIn("가구/인테리어", response.json()["category"])
        user = User.objects.get(phone_number="01033334444")
        self.assertEqual(user.interest, "10" + "1" * 15)


class GetUserCategoryTestCase(TestCase):
    @classmethod
    def setUp(cls):
        cls.user = UserFactory(
            phone_number="01011112222",
            email="wafflemarket@test.com",
            username="steve",
            interest="11001100110011001",
        )
        cls.user_token = "JWT " + jwt_token_of(User.objects.get(phone_number="01011112222"))

    def test_get_category_success(self):
        response = self.client.get("/api/v1/user/category/", HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json()["category"],
            [
                "디지털기기",
                "가구/인테리어",
                "여성의류",
                "게임/취미",
                "삽니다",
                "생활가전",
                "여성잡화",
                "남성패션/잡화",
                "기타 중고물품",
            ],
        )
