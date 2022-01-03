from factory.django import DjangoModelFactory

from user.models import User
from django.test import TestCase
from django.db import transaction
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

class PostUserTestCase(TestCase):
    
    @classmethod
    def setUpTestData(cls):

        cls.user = UserFactory(
            phone_number='01011112222',
            email='wafflemarket@test.com',
            username='steve'
        )

        cls.post_data = {
            'phone_number': '01022223333',
            'email': 'waffle@test.com',
            'username': 'mark'
        }

    def test_post_user_duplicate(self):
        # same phone_number
        data = self.post_data.copy()
        data.update({'phone_number': '01011112222'})
        with transaction.atomic():
           response = self.client.post('/api/v1/signup/', data=data)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

        user_count = User.objects.count()
        self.assertEqual(user_count, 1)

        # same email
        data = self.post_data.copy()
        data.update({'email': 'wafflemarket@test.com'})
        with transaction.atomic():
           response = self.client.post('/api/v1/signup/', data=data)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

        user_count = User.objects.count()
        self.assertEqual(user_count, 1)

    def test_post_user(self):
        # successively register user
        data = self.post_data
        response = self.client.post('/api/v1/signup/', data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = response.json()
        self.assertEqual(data["phone_number"], "01022223333")
        self.assertEqual(data["username"], "mark")
        self.assertEqual(data["logined"], True)
        self.assertEqual(data["first_login"], True)
        self.assertEqual(data["location_exists"], False)
        self.assertIn("token", data)

        user_count = User.objects.count()
        self.assertEqual(user_count, 2)