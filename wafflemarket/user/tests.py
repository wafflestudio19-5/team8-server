from factory.django import DjangoModelFactory

from user.models import User
from django.test import TestCase, TransactionTestCase
from rest_framework import status
import json

from user.serializers import jwt_token_of

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    @classmethod
    def create(cls, **kwargs):
        user = User.objects.create(**kwargs)
        user.set_password(kwargs.get('password', ''))
        user.save()
        return user

class PostUserTestCase(TransactionTestCase):
    
    @classmethod
    def setUp(cls):

        cls.user = UserFactory(
            phone_number='01011112222',
            username='steve'
        )

        cls.post_data = {
            'phone_number': '01022223333',
            'username': 'mark'
        }
    
    def test_post_user_wrong_information(self):
        # no phone_number
        data = self.post_data.copy()
        data.pop('phone_number')
        response = self.client.post('/api/v1/signup/', data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        res_data = response.json()
        self.assertEqual(res_data['phone_number'], ['This field is required.'])

        user_count = User.objects.count()
        self.assertEqual(user_count, 1)

        # invalid phone_number
        data = self.post_data.copy()
        data['phone_number'] = '010-1111-2222'
        response = self.client.post('/api/v1/signup/', data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        res_data = response.json()
        self.assertEqual(res_data['non_field_errors'], ['전화번호가 올바르지 않아요.'])

        user_count = User.objects.count()
        self.assertEqual(user_count, 1)

        # no username
        data = self.post_data.copy()
        data.pop('username')
        response = self.client.post('/api/v1/signup/', data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        res_data = response.json()
        self.assertEqual(res_data['username'], ['This field is required.'])

        user_count = User.objects.count()
        self.assertEqual(user_count, 1)

        # invalid username
        data = self.post_data.copy()
        data['username'] = 'waffle!'
        response = self.client.post('/api/v1/signup/', data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        res_data = response.json()
        self.assertEqual(res_data['non_field_errors'], ['닉네임은 띄어쓰기 없이 영문 한글 숫자만 가능해요.'])

        user_count = User.objects.count()
        self.assertEqual(user_count, 1)

    def test_post_user_duplicate(self):
        # same phone_number(=login)
        data = self.post_data.copy()
        data.update({'phone_number': '01011112222'})
        response = self.client.post('/api/v1/signup/', data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        res_data = response.json()
        self.assertEqual(res_data['phone_number'], '01011112222')
        self.assertEqual(res_data['username'], 'steve')
        self.assertEqual(res_data['logined'], True)
        self.assertEqual(res_data['first_login'], True)
        self.assertEqual(res_data['location_exists'], False)
        self.assertIn('token', res_data)

        user_count = User.objects.count()
        self.assertEqual(user_count, 1)

    def test_post_user_sucess(self):
        # successively register user
        data = self.post_data.copy()
        response = self.client.post('/api/v1/signup/', data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        res_data = response.json()
        self.assertEqual(res_data['phone_number'], '01022223333')
        self.assertEqual(res_data['username'], 'mark')
        self.assertEqual(res_data['logined'], True)
        self.assertEqual(res_data['first_login'], True)
        self.assertEqual(res_data['location_exists'], False)
        self.assertIn('token', res_data)

        user_count = User.objects.count()
        self.assertEqual(user_count, 2)

        user = User.objects.get(phone_number='01022223333')
        self.assertEqual(user.username, 'mark')
        self.assertIsNone(user.location)
        self.assertIsNotNone(user.created_at)
        self.assertIsNotNone(user.last_login)
        self.assertTrue(user.is_active)


