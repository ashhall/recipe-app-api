from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse('user:create')

TOKEN_URL = reverse('user:token')

VALID_PAYLOAD = {
    'name': 'Test Name',
    'email': 'test@gmail.com',
    'password': 'testpassword'
}


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    '''Test the users API (public)'''

    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user_success(self):
        '''Test creating user with valid payload is successful'''
        res = self.client.post(CREATE_USER_URL, VALID_PAYLOAD)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(**res.data)
        self.assertTrue(user.check_password(VALID_PAYLOAD['password']))
        self.assertNotIn('password', res.data)

    def test_user_exists(self):
        '''Test creating a user with duplicate data fails'''
        create_user(**VALID_PAYLOAD)

        res = self.client.post(CREATE_USER_URL, VALID_PAYLOAD)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        '''Test that user creation fails when password under 5 char'''
        short_pass_payload = {
            'name': 'Test Name',
            'email': 'test@gmail.com',
            'password': '1234'
        }

        res = self.client.post(CREATE_USER_URL, short_pass_payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=short_pass_payload['email']
        ).exists()
        self.assertFalse(user_exists)

    def test_create_token(self):
        '''Test that a user token is created'''
        create_user(**VALID_PAYLOAD)
        res = self.client.post(TOKEN_URL, VALID_PAYLOAD)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('token', res.data)

    def test_create_token_invalid_credentials(self):
        '''Test that token is not created if invalid credentials are given'''
        create_user(**VALID_PAYLOAD)
        invalid_cred_payload = {
            'email': VALID_PAYLOAD['email'],
            'password': 'invalid'
        }

        res = self.client.post(TOKEN_URL, invalid_cred_payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', res.data)

    def test_create_token_nonexistant_user(self):
        '''Test that token is not created if user doesn't exist'''
        res = self.client.post(TOKEN_URL, VALID_PAYLOAD)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', res.data)

    def test_create_token_missing_field(self):
        '''Test that email and password are required'''
        missing_pass_payload = {
            'name': 'Test Name',
            'email': 'test@gmail.com',
            'password': ''
        }

        res = self.client.post(TOKEN_URL, missing_pass_payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', res.data)
