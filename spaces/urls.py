from django.urls import path
from .views import (PartnerUpdate, ContactAPIView, LoginAPIView,
                    BasketAPIView, ConfirmBookingAPIView, BookingListAPIView)

urlpatterns = [
    path('login/', LoginAPIView.as_view(), name='login'),
    path('partner-update/', PartnerUpdate.as_view(), name='partner-update'),
    path('contacts/', ContactAPIView.as_view(), name='contacts-list'),
    path('contacts/<int:pk>/', ContactAPIView.as_view(), name='contacts-detail'),
    path('basket/', BasketAPIView.as_view(), name='basket'),
    path('basket/<int:pk>/', BasketAPIView.as_view(), name='basket-item-delete'),
    path('booking/<int:pk>/confirm/', ConfirmBookingAPIView.as_view(), name='confirm-booking'),
    path('bookings/', BookingListAPIView.as_view(), name='bookings'),
]