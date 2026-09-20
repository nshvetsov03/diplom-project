from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from requests import get
from yaml import load as load_yaml, Loader
from rest_framework.permissions import AllowAny
from django.core.mail import send_mail

from .models import (Location, Category, Space, SpaceDetails, Amenity,
                     SpaceAmenity, Contact, User, Booking, BookingItem, ConfirmEmailToken)
from .serializers import ContactSerializer, SpaceDetailsSerializer, BookingItemSerializer, BookingSerializer


# Create your views here.

class PartnerUpdate(APIView):
    """
    класс для обновления прайса от владельца коворкинга
    """

    def post(self, request, *args, **kwargs):
        # Проверяем аутентификацию
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Error': 'Log in required'}, status=status.HTTP_403_FORBIDDEN)

        # Получаем URL из запроса
        url = request.data.get('url')
        if url:
            # Валидируем URL
            validate_url = URLValidator()
            try:
                validate_url(url)
            except ValidationError as e:
                return Response({'Status': False, 'Error': str(e)})
            else:
                # Скачиваем YAML файл
                stream = get(url).content
                data = load_yaml(stream, Loader=Loader)

                # Создаем/находим Location
                location_data = data.get('location', {})
                location, _ = Location.objects.get_or_create(
                    name=location_data.get('name', 'Неизвестная локация'),
                    defaults={
                        'url': location_data.get('url', ''),
                        'address': location_data.get('address', ''),
                        'filename': url
                    }
                )

                # Создаем категории
                category_mapping = {}
                for category in data.get('categories', []):
                    category_object, _ = Category.objects.get_or_create(
                        name=category['name']
                    )
                    category_mapping[category['id']] = category_object
                    category_object.locations.add(location)

                # Удаляем старые SpaceDetails для этой локации (обновление прайса)
                SpaceDetails.objects.filter(location=location).delete()

                # Создаем Space и SpaceDetails
                for item in data.get('spaces', []):
                    category = category_mapping.get(item['category'])

                    space, _ = Space.objects.get_or_create(
                        name=item['name'],
                        defaults={'category': category}
                    )

                    space_detail = SpaceDetails.objects.create(
                        space=space,
                        location=location,
                        external_id=item['id'],
                        price=item['price'],
                        free_seat=item['free_seat']
                    )

                    # Создаем параметры (Amenity + SpaceAmenity)
                    for param_name, param_value in item.get('parameters', {}).items():
                        parameter_object, _ = Amenity.objects.get_or_create(name=param_name)
                        SpaceAmenity.objects.create(
                            space_detail=space_detail,
                            amenity=parameter_object,
                            value=str(param_value)
                        )

                return Response({'Status': True})

        return Response({'Status': False, 'Error': 'Не указан URL'})

class ContactAPIView(APIView):
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {'Status': False, 'Error': 'Log in required'},
                status=status.HTTP_403_FORBIDDEN
            )
        contacts = Contact.objects.filter(user=request.user)
        serializer = ContactSerializer(contacts, many=True)
        return Response(
            {'Status': True, 'contacts': serializer.data},
            status=status.HTTP_200_OK
        )

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {'Status': False, 'Error': 'Log in required'},
                status=status.HTTP_403_FORBIDDEN
            )
        data = request.data
        serializers = ContactSerializer(data=data)
        if serializers.is_valid():
            serializers.save(user=request.user)
            return Response(
                {'Status': True, 'data': serializers.data},
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                {'Status': False, 'Errors': serializers.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

    def delete(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {'Status': False, 'Error': 'Log in required'},
                status=status.HTTP_403_FORBIDDEN
            )
        contact_id = kwargs.get('pk')
        contact = Contact.objects.filter(id=contact_id, user=request.user).first()
        if not contact:
            return Response(
                {'Status': False, 'Error': 'Contact not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        else:
            contact.delete(
            )
            return Response(
                {'Status': True}, status=status.HTTP_200_OK
            )


class LoginAPIView(APIView):
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')

        # Ищем пользователя
        user = User.objects.filter(email=email).first()

        # Проверяем, что пользователь существует и пароль верный
        if not user or not user.check_password(password):
            return Response(
                {'Status': False, 'Error': 'Неверный email или пароль'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Получаем или создаем токен
        token, created = Token.objects.get_or_create(user=user)

        return Response(
            {'Status': True, 'token': token.key},
            status=status.HTTP_200_OK
        )


class RegistrationAPIView(APIView):
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')
        name_user = request.data.get('name_user')
        surname_user = request.data.get('surname_user')

        if User.objects.filter(email=email).exists():
            return Response(
                {'Status': False, 'Error': 'Пользователь с таким email уже существует'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = User.objects.create_user(
            email=email,
            password=password,
            name_user=name_user,
            surname_user=surname_user,
            is_active=False
        )

        token, created = Token.objects.get_or_create(user=user)

        return Response(
            {'Status': True, 'token': token.key},
            status=status.HTTP_201_CREATED
        )


class SpaceAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, *args, **kwargs):
        spaces = SpaceDetails.objects.all()
        serializer = SpaceDetailsSerializer(spaces, many=True)
        return Response(
            {'Status': True, 'spaces': serializer.data},
            status=status.HTTP_200_OK
        )


class BasketAPIView(APIView):
    """
    View для работы с корзиной (просмотр, добавление, удаление)
    """
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {'Status': False, 'Error': 'Log in required'},
                status=status.HTTP_403_FORBIDDEN
            )
        booking = Booking.objects.filter(user=request.user, status='pending').first()
        if not booking:
            return Response(
                {'Status': True, 'basket': None, 'message': 'Корзина пуста'},
                status=status.HTTP_200_OK
            )
        serializer = BookingSerializer(booking)
        return Response(
            {'Status': True, 'basket': serializer.data},
            status=status.HTTP_200_OK
        )

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {'Status': False, 'Error': 'Log in required'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Получаем данные и преобразуем в нужные типы
        space_detail_id = request.data.get('space_detail')
        quantity = request.data.get('quantity', 1)
        contact_id = request.data.get('contact')

        # Преобразуем в числа (если они есть)
        try:
            space_detail_id = int(space_detail_id) if space_detail_id else None
            quantity = int(quantity) if quantity else 1
            contact_id = int(contact_id) if contact_id else None
        except (ValueError, TypeError):
            return Response(
                {'Status': False, 'Error': 'Некорректные данные'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not space_detail_id or not contact_id:
            return Response(
                {'Status': False, 'Error': 'Не указаны space_detail или contact'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Ищем или создаем корзину
        booking, created = Booking.objects.get_or_create(
            user=request.user,
            status='pending',
            defaults={'contact_id': contact_id}
        )

        # Ищем или создаем позицию
        item, item_created = BookingItem.objects.get_or_create(
            booking=booking,
            space_detail_id=space_detail_id,
            defaults={'quantity': quantity}
        )

        # Обновляем количество, если позиция уже была
        if not item_created:
            item.quantity = quantity
            item.save()

        serializer = BookingSerializer(booking)
        return Response(
            {'Status': True, 'basket': serializer.data},
            status=status.HTTP_200_OK
        )

    def delete(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {'Status': False, 'Error': 'Log in required'},
                status=status.HTTP_403_FORBIDDEN
            )

        item_id = kwargs.get('pk')
        if not item_id:
            return Response(
                {'Status': False, 'Error': 'Не указан ID позиции'},
                status=status.HTTP_400_BAD_REQUEST
            )

        booking = Booking.objects.filter(user=request.user, status='pending').first()
        if not booking:
            return Response(
                {'Status': False, 'Error': 'Корзина не найдена'},
                status=status.HTTP_404_NOT_FOUND
            )

        item = BookingItem.objects.filter(id=item_id, booking=booking).first()
        if not item:
            return Response(
                {'Status': False, 'Error': 'Позиция не найдена в корзине'},
                status=status.HTTP_404_NOT_FOUND
            )

        item.delete()

        serializer = BookingSerializer(booking)
        return Response(
            {'Status': True, 'basket': serializer.data},
            status=status.HTTP_200_OK
        )


class ConfirmBookingAPIView(APIView):
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Error': 'Log in required'}, status=status.HTTP_403_FORBIDDEN)

        booking_id = kwargs.get('pk')
        booking = Booking.objects.filter(id=booking_id, user=request.user, status='pending').first()

        if not booking:
            return Response({'Status': False, 'Error': 'Бронирование не найдено'}, status=status.HTTP_404_NOT_FOUND)

        # Проверка на пустую корзину
        if not booking.items.exists():
            return Response({'Status': False, 'Error': 'Корзина пуста, добавьте товары перед подтверждением'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Обновление контакта при подтверждении
        new_contact_id = request.data.get('contact')
        if new_contact_id:
            contact = Contact.objects.filter(id=new_contact_id, user=request.user).first()
            if contact:
                booking.contact = contact
                booking.save()

        # Меняем статус
        booking.status = 'confirmed'
        booking.save()

        # Отправляем email
        send_mail(
            subject='Подтверждение бронирования коворкинга',
            message=f'Здравствуйте! Ваше бронирование №{booking.id} успешно подтверждено.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[request.user.email],
            fail_silently=False,
        )

        serializer = BookingSerializer(booking)
        return Response({'Status': True, 'booking': serializer.data}, status=status.HTTP_200_OK)


class BookingListAPIView(APIView):
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Error': 'Log in required'}, status=status.HTTP_403_FORBIDDEN)

        bookings = Booking.objects.filter(user=request.user).order_by('-dt')
        serializer = BookingSerializer(bookings, many=True)

        return Response({'Status': True, 'bookings': serializer.data}, status=status.HTTP_200_OK)


class ConfirmRegistrationAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        token_key = request.data.get('token')

        if not email or not token_key:
            return Response(
                {'Status': False, 'Error': 'Не указаны email или token'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = User.objects.filter(email=email).first()
        if not user:
            return Response(
                {'Status': False, 'Error': 'Пользователь не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Ищем токен
        token = ConfirmEmailToken.objects.filter(user=user, key=token_key).first()
        if not token:
            return Response(
                {'Status': False, 'Error': 'Неверный токен подтверждения'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Активируем пользователя и удаляем токен
        user.is_active = True
        user.save()
        token.delete()

        return Response(
            {'Status': True, 'message': 'Регистрация успешно подтверждена'},
            status=status.HTTP_200_OK
        )


class SpaceDetailAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        space_id = kwargs.get('pk')
        space = SpaceDetails.objects.filter(id=space_id).first()
        if not space:
            return Response(
                {'Status': False, 'Error': 'Пространство не найдено'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = SpaceDetailsSerializer(space)
        return Response(
            {'Status': True, 'space': serializer.data},
            status=status.HTTP_200_OK
        )