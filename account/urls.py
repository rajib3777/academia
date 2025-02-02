from django.urls import path
from account.apis import LoginSerializer, UserUpdateAPIView, UserListAPIView, RegistrationAPIView

app_name = "users"
urlpatterns = [
    path('login/', LoginSerializer, name='login'),
    path('users/', UserListAPIView.as_view(), name='user-list'),
    path('user/<int:pk>/', UserUpdateAPIView.as_view(), name='user-update'),
    path('register/', RegistrationAPIView.as_view(), name='register'),
]