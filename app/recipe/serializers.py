from rest_framework import serializers

from core.models import Ingredient, Tag


class IngredientSerializer(serializers.ModelSerializer):
    '''Serializer for the ingredient object'''

    class Meta:
        model = Ingredient
        fields = ('id', 'name')
        read_only_fields = ('id',)


class TagSerializer(serializers.ModelSerializer):
    '''Serializer for the tag object'''

    class Meta:
        model = Tag
        fields = ('id', 'name')
        read_only_fields = ('id',)
