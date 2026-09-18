from django.urls import path
from .views import PartnerUpdate, ContactAPIView, LoginAPIView

urlpatterns = [
    path('login/', LoginAPIView.as_view(), name='login'),
    path('partner-update/', PartnerUpdate.as_view(), name='partner-update'),
    path('contacts/', ContactAPIView.as_view(), name='contacts-list'),
    path('contacts/<int:pk>/', ContactAPIView.as_view(), name='contacts-detail'),
]