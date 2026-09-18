from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from requests import get
from yaml import load as load_yaml, Loader

from .models import Location, Category, Space, SpaceDetails, Amenity, SpaceAmenity, Contact, User
from .serializers import ContactSerializer, SpaceDetailsSerializer


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
                            parameter=parameter_object,
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
            surname_user=surname_user
        )

        token, created = Token.objects.get_or_create(user=user)

        return Response(
            {'Status': True, 'token': token.key},
            status=status.HTTP_201_CREATED
        )


class SpaceAPIView(APIView):
    def get(self, request, *args, **kwargs):
        spaces = SpaceDetails.objects.all()
        serializer = SpaceDetailsSerializer(spaces, many=True)
        return Response(
            {'Status': True, 'spaces': serializer.data},
            status=status.HTTP_200_OK
        )