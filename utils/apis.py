from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from utils.models import OTPVerification
from utils.serializers.serializers import SendOTPSerializer, VerifyOTPSerializer
from utils.utils import generate_otp, send_sms
from utils.choices import OTP


class SendOTPView(APIView):
    """
    API View for send OTP (One-Time Password).

    For detailed documentation, refer to:
    `docs/send_otp_view.md`
    """
    permission_classes = ()
    authentication_classes = ()

    def post(self, request, *args, **kwargs):
        serializer = SendOTPSerializer(data=request.data)

        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']

            otp = generate_otp()

            otp_obj, created = OTPVerification.objects.update_or_create(
                phone_number=phone_number,
                defaults={"otp": otp, "is_verified": False}
            )

            if otp_obj:
                if send_sms(
                    phone_number=phone_number,
                    message=f"Your OTP is {otp}",
                    sms_type=OTP,
                ):
                    return JsonResponse({"message": "OTP sent successfully."})
                return Response({'error': 'Something wrong! OTP can not send.'}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'error': 'Something wrong! OTP can not create.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyOTPView(APIView):
    """
    API View for verifying OTP (One-Time Password).

    For detailed documentation, refer to:
    `docs/verify_otp_view.md`
    """
    permission_classes = ()
    authentication_classes = ()

    def post(self, request, *args, **kwargs):
        serializer = VerifyOTPSerializer(data=request.data)

        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            otp = serializer.validated_data['otp']

            try:
                otp_instance = get_object_or_404(OTPVerification, phone_number=phone_number)

                if otp_instance.is_verified:
                    return JsonResponse({"error": "Phone number already verified."})
                if otp_instance.is_expired():
                    return Response({'error': 'OTP has expired.'}, status=status.HTTP_400_BAD_REQUEST)

                if otp_instance.otp == otp:
                    otp_instance.is_verified = True
                    otp_instance.save()
                    #TODO OTP is valid; delete it
                    #otp_instance.delete()
                    return Response({'message': 'OTP verified successfully.'}, status=status.HTTP_200_OK)

                return Response({'error': 'Invalid OTP.'}, status=status.HTTP_400_BAD_REQUEST)
            except OTPVerification.DoesNotExist:
                return Response({'error': 'Invalid phone number.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
