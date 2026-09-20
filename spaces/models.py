from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import ForeignKey, CASCADE
from django_rest_passwordreset.tokens import get_token_generator

BOOKING_STATUS_CHOICES = (
    ('pending', 'Ожидает подтверждения'),
    ('confirmed', 'Подтверждено'),
    ('cancelled', 'Отменено'),
    ('completed', 'Завершено'),
)

class UserManager(BaseUserManager):
    """
    Миксин для управления пользователями
    """

    def _create_user(self, email, password, **extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Стандартная модель юзера
    """
    objects = UserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    username = models.CharField(max_length=150, blank=True, null=True)
    name_user = models.CharField(verbose_name='Имя пользователя',max_length=20, blank=False)
    surname_user = models.CharField(verbose_name='Фамилия пользователя', max_length=30, blank=False)
    middle_name_user = models.CharField(verbose_name='Отчество пользователя', max_length=30, blank=True)
    email = models.EmailField(verbose_name='email', max_length=50, unique=True, blank=False)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Список пользователей'
        ordering = ('name_user',)

    def __str__(self):
        return f'{self.name_user} {self.surname_user}'

    def get_full_name_with_patronymic(self):
        """Возвращает полное имя с отчеством (если есть)"""
        if self.middle_name_user:
            return f'{self.name_user} {self.surname_user} {self.middle_name_user}'
        return f'{self.name_user} {self.surname_user}'


class Location(models.Model):
    name = models.CharField(verbose_name='Название', max_length=30)
    url = models.CharField(verbose_name='Ссылка на сайт', max_length=100)
    address = models.CharField(verbose_name='Адрес', max_length=60)
    filename = models.CharField(verbose_name='Имя файла импорта', max_length=100, blank=True)

    class Meta:
        verbose_name = 'Локация'
        verbose_name_plural = 'Локации'
        ordering = ('name',)

    def __str__(self):
        return self.name

    def categories_count(self):
        """Возвращает количество категорий в этой локации"""
        return self.categories.count()


class Category(models.Model):
    name = models.CharField(verbose_name='Категория', max_length=30)
    locations = models.ManyToManyField(Location, verbose_name='Локации', related_name='categories')

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ('name',)

    def __str__(self):
        return self.name

    def locations_count(self):
        """Возвращает количество локаций с этой категорией"""
        return self.locations.count()


class Space(models.Model):
    name = models.CharField(verbose_name='Название пространства', max_length=50)
    category = models.ForeignKey(
        Category,
        verbose_name='Категория',
        null=True,
        blank=True,
        related_name='spaces',
        on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Пространство'
        verbose_name_plural = 'Пространства'
        ordering = ('name',)

    def __str__(self):
        return self.name


class SpaceDetails(models.Model):
    price = models.PositiveIntegerField(verbose_name='Цена за час', blank=False)
    free_seat = models.PositiveIntegerField(verbose_name='Количество свободных мест', blank=False)
    external_id = models.PositiveIntegerField(verbose_name='Внешний ИД')
    space = models.ForeignKey(Space, verbose_name='Пространство', related_name='space_info', blank=True,
                              on_delete=models.CASCADE)
    location = models.ForeignKey(Location, verbose_name='Локации', related_name='location_info', blank=True,
                                 on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Информация о коворкинге'
        verbose_name_plural = 'Информация о коворкингах'
        constraints = [
            models.UniqueConstraint(
                fields=['space', 'location', 'external_id'],
                name='unique_space_details'
            )
        ]

    def __str__(self):
        return f'{self.space.name} в {self.location.name} - {self.price}р/ч'


class Amenity(models.Model):
    name = models.CharField(verbose_name='Название', max_length=70)

    class Meta:
        verbose_name = 'Имя параметра'
        verbose_name_plural = 'Список имен параметров'
        ordering = ('-name',)

    def __str__(self):
        return self.name


class SpaceAmenity(models.Model):
    space_detail = models.ForeignKey(
        SpaceDetails,
        verbose_name='Информация о продукте',
        related_name='space_amenity',
        blank=True,
        on_delete=models.CASCADE
    )
    amenity = models.ForeignKey(
        Amenity,
        verbose_name='Параметр',
        related_name='space_amenity',
        blank=True,
        on_delete=models.CASCADE
    )
    value = models.CharField(verbose_name='Значение', max_length=100)

    class Meta:
        verbose_name = 'Параметр'
        verbose_name_plural = "Список параметров"
        constraints = [
            models.UniqueConstraint(fields=['space_detail', 'amenity'], name='unique_space_amenity'),
        ]


class Contact(models.Model):
    user = models.ForeignKey(User, verbose_name="Пользователь", related_name='contacts', on_delete=models.CASCADE)
    city = models.CharField(max_length=50, verbose_name='Город')
    street = models.CharField(max_length=100, verbose_name='Улица')
    house = models.CharField(max_length=15, verbose_name='Дом', blank=True)
    structure = models.CharField(max_length=15, verbose_name='Корпус', blank=True)
    building = models.CharField(max_length=15, verbose_name='Строение', blank=True)
    apartment = models.CharField(max_length=15, verbose_name='Квартира', blank=True)
    phone = models.CharField(max_length=20, verbose_name='Телефон')

    class Meta:
        verbose_name = 'Контакт'
        verbose_name_plural = 'Контакты'

    def __str__(self):
        return f'{self.city} {self.street} {self.house}'


class Booking(models.Model):
    user = models.ForeignKey(User, verbose_name="Пользователь", related_name='bookings', on_delete=models.CASCADE)
    dt = models.DateTimeField(auto_now_add=True)
    status = models.CharField(verbose_name='Статус', choices=BOOKING_STATUS_CHOICES, max_length=15, default='pending')
    contact = models.ForeignKey(Contact, verbose_name='Контакты', related_name='bookings', on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Бронирование'
        verbose_name_plural = 'Бронирования'

    def __str__(self):
        return  f'{self.dt}'


class BookingItem(models.Model):
    booking = models.ForeignKey(
        Booking,
        verbose_name='Бронирование',
        related_name='items',
        on_delete=models.CASCADE
    )
    space_detail = models.ForeignKey(
        SpaceDetails,
        verbose_name='Пространство',
        related_name='booking_items',
        on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField(
        verbose_name='Количество часов',
        default=1
    )

    class Meta:
        verbose_name = 'Позиция бронирования'
        verbose_name_plural = 'Позиции бронирования'
        constraints = [
            models.UniqueConstraint(
                fields=['booking', 'space_detail'],
                name='unique_booking_item'
            ),
        ]

    def __str__(self):
        return f'{self.space_detail.space.name} - {self.quantity}ч'


class ConfirmEmailToken(models.Model):
    class Meta:
        verbose_name = 'Токен подтверждения Email'
        verbose_name_plural = 'Токены подтверждения Email'

    @staticmethod
    def generate_key():
        return get_token_generator().generate_token()

    user = models.ForeignKey(
        User,
        related_name='confirm_email_tokens',
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    key = models.CharField(
        'Ключ',
        max_length=64,
        db_index=True,
        unique=True
    )

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super(ConfirmEmailToken, self).save(*args, **kwargs)

    def __str__(self):
        return f"Токен подтверждения для {self.user}"