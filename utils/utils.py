import random
import requests
from django.utils.timezone import now
from django.core.exceptions import ValidationError
from typing import Optional, Dict, Any
import logging
from django.conf import settings
from utils.choices import FAILED, SENT, QUEUE
from account.models import User
from utils.models import OTPVerification, SMSHistory

logger = logging.getLogger(__name__)

def generate_otp():
    return f"{random.randint(100000, 999999)}"

def send_sms(phone_number, message, sms_type):
    # not in use
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


def save_sms_history(
    *,
    created_by: Optional['User'],
    created_for: Optional['User'],
    phone_number: str,
    message: str,
    sms_type: str,
    status: str = QUEUE,
) -> 'SMSHistory':
    # Not in use
    """
    Global method to save SMSHistory for any type of SMS.

    Args:
        created_by: User who initiated the SMS.
        created_for: User who is the recipient.
        phone_number: Recipient's phone number.
        message: SMS content.
        sms_type: Type of SMS (from SMS_TYPE_CHOICES).
        status: Delivery status (from STATUS_CHOICES).
    Returns:
        SMSHistory instance.
    """
    from utils.models import SMSHistory

    try:
        sms_data = {
            'created_by': created_by,
            'created_for': created_for,
            'phone_number': phone_number,
            'message': message,
            'sms_type': sms_type,
            'status': status,
        }

        sms_history = SMSHistory.objects.create(**sms_data)
        logger.info(f'SMSHistory saved: {sms_history}')
        return sms_history
    except Exception as e:
        logger.error(f'Error saving SMSHistory: {e}')
        raise