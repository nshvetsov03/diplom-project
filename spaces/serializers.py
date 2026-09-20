from rest_framework import serializers
from .models import Contact, SpaceDetails, Booking, BookingItem

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


class BookingItemSerializer(serializers.ModelSerializer):
    """
    Сериализатор для позиции бронирования
    """
    space_name = serializers.CharField(source='space_detail.space.name', read_only=True)
    location_name = serializers.CharField(source='space_detail.location.name', read_only=True)
    price_per_hour = serializers.IntegerField(source='space_detail.price', read_only=True)
    total_item_price = serializers.SerializerMethodField()

    class Meta:
        model = BookingItem
        fields = ['id', 'space_detail', 'quantity', 'space_name', 'location_name', 'price_per_hour', 'total_item_price']

    def get_total_item_price(self, obj):
        """Считаем стоимость позиции: цена * количество часов"""
        return obj.space_detail.price * obj.quantity


class BookingSerializer(serializers.ModelSerializer):
    """
    Сериализатор для бронирования
    """
    items = BookingItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()
    contact_info = serializers.CharField(source='contact', read_only=True)

    class Meta:
        model = Booking
        fields = ['id', 'dt', 'status', 'contact', 'contact_info', 'items', 'total_price']

    def get_total_price(self, obj):
        """Считаем общую стоимость бронирования"""
        total = 0
        for item in obj.items.all():
            total += item.space_detail.price * item.quantity
        return total