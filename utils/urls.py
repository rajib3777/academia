from django.urls import path
from utils.apis import SendOTPView, VerifyOTPView

app_name = "utils"

urlpatterns = [
    path('send-otp/', SendOTPView.as_view(), name='send_otp'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify_otp'),
]
