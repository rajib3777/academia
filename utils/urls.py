from django.urls import path
from utils.apis import SendOTPView, VerifyOTPView, DivisionListAPIView, DistrictListAPIView, UpazilaListAPIView

app_name = "utils"

urlpatterns = [
    path('send-otp/', SendOTPView.as_view(), name='send_otp'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify_otp'),

    path('divisions/', DivisionListAPIView.as_view(), name='division-list'),
    path('districts/', DistrictListAPIView.as_view(), name='district-list'),
    path('upazilas/', UpazilaListAPIView.as_view(), name='upazila-list'),

]
