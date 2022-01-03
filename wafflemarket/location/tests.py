from factory.django import DjangoModelFactory

from user.models import User
from location.models import Location, LocationNeighborhood
from django.test import TestCase, TransactionTestCase
from django.db import transaction
from rest_framework import status
import json

from user.serializers import jwt_token_of, UserSerializer
from user.tests import UserFactory


class LocationFactory(DjangoModelFactory):
    class Meta:
        model = Location

class PostLocationTestCase(TestCase):
    
    @classmethod
    def setUp(cls):

        cls.user = UserFactory(
            phone_number='01011112222',
            email='wafflemarket@test.com',
            username='steve'
        )
        cls.user_token = 'JWT ' + jwt_token_of(User.objects.get(phone_number='01011112222'))

        cls.location1 = LocationFactory(
            code='1111011700',
            place_name='서울특별시 종로구 당주동'
        )
        cls.location2 = LocationFactory(
            code='1111011100',
            place_name='서울특별시 종로구 옥인동'
        )
        LocationNeighborhood.objects.create(location=cls.location1,neighborhood=cls.location2)

        cls.post_data = {
            'location_code': '1111011700'
        }
    
    def test_post_location_wrong_information(self):
        # no token
        data = self.post_data.copy()
        response = self.client.post('/api/v1/location/', data=data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.assertEqual(self.user.location, None)

        # no location code
        data = self.post_data.copy()
        data.pop('location_code')
        response = self.client.post('/api/v1/location/', data=data, HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        res_data = response.json()
        self.assertEqual(res_data['location_code'], ['This field is required.'])
        self.assertEqual(self.user.location, None)

        # invalid location code
        data = self.post_data.copy()
        data['location_code'] = '1111011701'
        response = self.client.post('/api/v1/location/', data=data, HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        res_data = response.json()
        self.assertEqual(res_data['non_field_errors'], ['올바른 지역코드가 아닙니다.'])
        self.assertEqual(self.user.location, None)

    def test_post_location_sucess(self):
        # successively change user's location info
        data = self.post_data.copy()
        response = self.client.post('/api/v1/location/', data=data, HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        res_data = response.json()
        self.assertEqual(res_data["username"], "steve")
        self.assertEqual(User.objects.get(location=self.location1).phone_number, '01011112222')