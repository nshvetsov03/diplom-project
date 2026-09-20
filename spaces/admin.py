from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import (
    User, Location, Category, Space, SpaceDetails,
    Amenity, SpaceAmenity, Contact, Booking, BookingItem
)

# 1. Inline для позиций заказа (чтобы видеть товары прямо в заказе)
class BookingItemInline(admin.TabularInline):
    model = BookingItem
    extra = 0
    readonly_fields = ('space_detail', 'quantity')

# 2. Админка для Заказов (Booking)
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_email', 'contact', 'status', 'dt', 'get_total_price')
    list_filter = ('status', 'dt')
    search_fields = ('user__email', 'user__name_user', 'user__surname_user')
    inlines = [BookingItemInline]
    readonly_fields = ('dt',)

    @admin.display(description='Email пользователя')
    def user_email(self, obj):
        return obj.user.email

    @admin.display(description='Общая сумма')
    def get_total_price(self, obj):
        total = sum(item.space_detail.price * item.quantity for item in obj.items.all())
        return f"{total} ₽"

# 3. Админка для Пользователей
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'name_user', 'surname_user', 'is_staff')
    list_filter = ('is_staff',)
    search_fields = ('email', 'name_user', 'surname_user')

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'city', 'phone')
    list_filter = ('city',)
    search_fields = ('user__email', 'city', 'phone')

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'address')
    search_fields = ('name', 'address')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Space)
class SpaceAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    list_filter = ('category',)
    search_fields = ('name',)

@admin.register(SpaceDetails)
class SpaceDetailsAdmin(admin.ModelAdmin):
    list_display = ('id', 'space', 'location', 'price', 'free_seat', 'external_id')
    list_filter = ('location', 'space__category')
    search_fields = ('space__name', 'location__name')

@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(SpaceAmenity)
class SpaceAmenityAdmin(admin.ModelAdmin):
    list_display = ('space_detail', 'value')
    search_fields = ('value', 'space_detail__space__name')