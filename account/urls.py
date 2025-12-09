from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from account.apis import LoginAPIView, UserUpdateAPIView, UserListAPIView, RegistrationAPIView, RoleListAPIView, RoleMenuPermissionListView, RoleMenuPermissionNestedListView, GenerateRecoveryOTPAPIView
from account.views import ChangePasswordView, ResetPasswordView, AccountDetailView, AccountUpdateView, NavbarAccountInfoView

app_name = "users"
urlpatterns = [
    path('login/', LoginAPIView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('users/', UserListAPIView.as_view(), name='user-list'),
    path('user/<int:pk>/', UserUpdateAPIView.as_view(), name='user-update'),
    path('registration/', RegistrationAPIView.as_view(), name='registration'),
    path('roles/', RoleListAPIView.as_view(), name='role-list'),
    path('role-menu-permissions/', RoleMenuPermissionListView.as_view(), name='role-menu-permissions'),
    path('role-menu-permissions-nested/', RoleMenuPermissionNestedListView.as_view(), name='role-menu-permissions-nested'),
    path('account/details/', AccountDetailView.as_view(), name='account-details'),
    path('account/update/', AccountUpdateView.as_view(), name='account-update'),
    path('navbar-account-info/', NavbarAccountInfoView.as_view(), name='navbar-account-info'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('generate-recovery-otp/', GenerateRecoveryOTPAPIView.as_view(), name="generate_recovery_otp"),
]
