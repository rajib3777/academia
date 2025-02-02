from rest_framework import serializers

class SendOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)

class VerifyOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    otp = serializers.CharField(max_length=6)


# https://chatgpt.com/c/67968737-06d4-8010-ae46-b284984da583