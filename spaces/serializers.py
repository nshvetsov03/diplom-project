from rest_framework import serializers
from .models import Contact, SpaceDetails

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ['id', 'city', 'street', 'house', 'structure', 'building', 'apartment', 'phone']


class SpaceDetailsSerializer(serializers.ModelSerializer):
    space_name = serializers.CharField(source='space.name', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)

    class Meta:
        model = SpaceDetails
        fields = ['id', 'price', 'free_seat', 'space_name', 'location_name']
