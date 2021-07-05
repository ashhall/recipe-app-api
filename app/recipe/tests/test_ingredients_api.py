from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient

from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse('recipe:ingredient-list')


class PublicIngredientsApiTest(TestCase):
    '''Test unauthenticated access of ingredients API'''

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        '''Test that login is required to access the endpoint'''
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTest(TestCase):
    '''Test authenticated access of ingredients API '''

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'test@gmail.com',
            'testpassword'
        )
        self.client.force_authenticate(user=self.user)

    def test_retrieve_ingredient_list(self):
        '''Test retrieving a list of ingredients'''
        Ingredient.objects.create(user=self.user, name='Ingredient1')
        Ingredient.objects.create(user=self.user, name='Ingredient2')

        res = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        '''Test that ingredients are returned for the authenticated user'''

        # create another user with an associated ingredient
        unauthenticated_user = get_user_model().objects.create_user(
            'test2@gmail.com',
            'testpassword2'
        )
        Ingredient.objects.create(
            user=unauthenticated_user,
            name='Ingredient Name Unauth'
        )

        # create an ingredient associated to the authenticated user
        ingredient = Ingredient.objects.create(
            user=self.user,
            name='Ingredient Name'
        )

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)

    def test_create_ingredient_successful(self):
        '''Test that ingredients are created successfully'''

        payload = {'name': 'Ingredient Name'}

        self.client.post(INGREDIENTS_URL, payload)

        ingredient_exists = Ingredient.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()

        self.assertTrue(ingredient_exists)

    def test_create_ingredient_invalid(self):
        '''Test creating a new ingredient with invalid payload fails'''
        payload = {'name': ''}

        res = self.client.post(INGREDIENTS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
