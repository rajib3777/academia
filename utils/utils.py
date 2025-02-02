import random
import requests
from django.utils.timezone import now
from django.core.exceptions import ValidationError
import logging
from django.conf import settings
from utils.choices import FAILED, SENT
from utils.models import OTPVerification, SMSHistory


def generate_otp():
    return f"{random.randint(100000, 999999)}"

def send_sms(phone_number, message, sms_type):
    """
    API View for send sms.

    For detailed documentation, refer to:
    `docs/send_sms.md`
    """
    global sms_history
    try:
        # Create SMS history record
        sms_history = SMSHistory.objects.create(phone_number=phone_number, message=message, sms_type=sms_type)

        # Retrieve SMS gateway configuration dynamically
        sms_gateway_url = settings.SMS_GATEWAY_URL
        api_key = settings.SMS_API_KEY
        sender_id = settings.SMS_SENDER_ID

        response = requests.post(sms_gateway_url, data={
            "api_key": api_key,
            "senderid": sender_id,
            "number": str(phone_number),
            "message": message
        })

        # Parse response and handle errors
        try:
            response_data = response.json()
        except ValueError:
            logging.error(f"Failed to parse response: {response.text}")
            sms_history.status = FAILED
            sms_history.failed_reason = "Invalid JSON response"
            sms_history.response_at = now()
            sms_history.save()
            return False

        response_code = response_data.get("response_code")

        # Check if SMS was sent successfully
        if response_code != 202:
            sms_history.status = FAILED
            sms_history.failed_reason = response_data.get("error_message", "Unknown error")
            sms_history.failed_status_code = response_code
            sms_history.response_at = now()
            sms_history.save()
            return False

        # Update SMS history as sent
        sms_history.status = SENT
        sms_history.response_at = now()
        sms_history.save()

        return True

    except requests.RequestException as e:
        # Log request errors
        logging.error(f"An error occurred while sending SMS: {str(e)}")
        sms_history.status = FAILED
        sms_history.failed_reason = str(e)
        sms_history.failed_status_code = None
        sms_history.response_at = now()
        sms_history.save()
        return False


def validate_phone_number(phone_number):
    otp_obj = OTPVerification.objects.filter(phone_number=phone_number, is_verified=True).first()
    if not otp_obj:
        raise ValidationError("Phone number not verified.")
