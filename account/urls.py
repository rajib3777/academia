from django.urls import path
from account.apis import LoginAPIView, UserUpdateAPIView, UserListAPIView, RegistrationAPIView

app_name = "users"
urlpatterns = [
    path('login/', LoginAPIView.as_view(), name='login'),
    path('users/', UserListAPIView.as_view(), name='user-list'),
    path('user/<int:pk>/', UserUpdateAPIView.as_view(), name='user-update'),
    path('registration/', RegistrationAPIView.as_view(), name='registration'),
]