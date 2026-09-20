from django.urls import path
from .views import (
    PartnerUpdate,
    ContactAPIView,
    LoginAPIView,
    RegistrationAPIView,
    SpaceAPIView,
    BasketAPIView,
    ConfirmBookingAPIView,
    BookingListAPIView,
    ConfirmRegistrationAPIView
)

urlpatterns = [
    path('registration/', RegistrationAPIView.as_view(), name='registration'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('spaces/', SpaceAPIView.as_view(), name='spaces'),
    path('contacts/', ContactAPIView.as_view(), name='contacts-list'),
    path('contacts/<int:pk>/', ContactAPIView.as_view(), name='contacts-detail'),
    path('basket/', BasketAPIView.as_view(), name='basket'),
    path('basket/<int:pk>/', BasketAPIView.as_view(), name='basket-item-delete'),
    path('booking/<int:pk>/confirm/', ConfirmBookingAPIView.as_view(), name='confirm-booking'),
    path('bookings/', BookingListAPIView.as_view(), name='bookings'),
    path('partner-update/', PartnerUpdate.as_view(), name='partner-update'),
    path('registration/confirm/', ConfirmRegistrationAPIView.as_view(), name='confirm-registration'),
]