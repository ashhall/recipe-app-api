from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse('user:create')

TOKEN_URL = reverse('user:token')

ME_URL = reverse('user:me')

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

    def test_user_already_exists(self):
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

        user_exists = get_user_model().objects.filter(
            email=short_pass_payload['email']
        ).exists()

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
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

    def test_retrieve_user_unauthorized(self):
        '''Test that authentication is required for user'''
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    '''Test API requests that require authentication'''

    def setUp(self):
        self.user = create_user(**VALID_PAYLOAD)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        '''Test retrieving profile for logged in user'''
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'name': self.user.name,
            'email': self.user.email
        })

    def test_post_my_account_not_allowed(self):
        '''Test that POST is not allowed on the my account url'''
        res = self.client.post(ME_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        '''Test updating the user profile for authenticated user'''
        new_payload = {
            'name': 'New Name',
            'password': 'newtestpassword'
        }
        res = self.client.patch(ME_URL, new_payload)

        self.user.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.name, new_payload['name'])
        self.assertTrue(self.user.check_password(new_payload['password']))
