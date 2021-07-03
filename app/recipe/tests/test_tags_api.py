from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag

from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')


class PublicTagsApiTests(TestCase):
    '''Test the publicly available tags API'''

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        '''Test that login is required for retrieving tags'''
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTests(TestCase):
    '''Test the authorized user tags API'''

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            'test@gmail.com',
            'testpassword'
        )

        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        '''Test retrieving tags'''
        Tag.objects.create(user=self.user, name='Tag Name 1')
        Tag.objects.create(user=self.user, name='Tag Name 2')

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        '''Test that tags returned are for the authenticated user'''

        # create another user with an associated tag
        unauthenticated_user = get_user_model().objects.create_user(
            'test2@gmail.com',
            'testpassword2'
        )
        Tag.objects.create(user=unauthenticated_user, name='Tag Name Unauth')

        # create a tag associated to the authenticated user
        tag = Tag.objects.create(user=self.user, name='Tag Name')

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)

    def test_create_tag_successful(self):
        '''Test that tags are created successfully'''

        payload = {'name': 'Tag Name'}

        self.client.post(TAGS_URL, payload)

        tag_exists = Tag.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()

        self.assertTrue(tag_exists)

    def test_create_tag_invalid(self):
        '''Test that creating a new tag with invalid payload fails'''
        payload = {'name': ''}

        res = self.client.post(TAGS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
