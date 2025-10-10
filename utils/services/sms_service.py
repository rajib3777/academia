import logging
import requests
from django.utils.timezone import now
from django.conf import settings
from typing import Optional, Dict, Any
from utils.choices import FAILED, SENT, QUEUE
from utils.selectors.sms_selector import SMSHistorySelector
from utils.models import SMSHistory
from account.models import User

logger = logging.getLogger(__name__)

class SMSService:
    """
    Service for sending SMS and saving SMS history.
    """

    def __init__(self):
        self.sms_selector = SMSHistorySelector()

    @staticmethod
    def send_sms() -> None:
        """
        Send SMS and save SMS history using service and selector.

        Args:
            sms: SMSHistory instance.

        Returns:
            True if sent, False otherwise.
        """
        sms_selector = SMSHistorySelector()
        sms_history = sms_selector.get_queue_sms()
        
        if not sms_history:
            return

        for sms in sms_history:
            try:
                sms_gateway_url = settings.SMS_GATEWAY_URL
                api_key = settings.SMS_API_KEY
                sender_id = settings.SMS_SENDER_ID

                response = requests.post(sms_gateway_url, data={
                    'api_key': api_key,
                    'senderid': sender_id,
                    'number': str(sms.phone_number),
                    'message': sms.message
                })

                # Parse response and handle errors
                try:
                    response_data = response.json()
                except ValueError:
                    logger.error(f'Failed to parse response: {response.text}')
                    SMSService.update_sms_status(
                        sms_history,
                        status=FAILED,
                        failed_reason='Invalid JSON response',
                        response_at=now()
                    )
                    return

                response_code = response_data.get('response_code')

                if response_code != 202:
                    SMSService.update_sms_status(
                        sms_history,
                        status=FAILED,
                        failed_reason=response_data.get('error_message', 'Unknown error'),
                        failed_status_code=response_code,
                        response_at=now()
                    )
                    return

                SMSService.update_sms_status(
                    sms_history,
                    status=SENT,
                    response_at=now()
                )
                return

            except requests.RequestException as e:
                logger.error(f'An error occurred while sending SMS: {str(e)}')
                SMSService.update_sms_status(
                    sms_history,
                    status=FAILED,
                    failed_reason=str(e),
                    failed_status_code=None,
                    response_at=now()
                )
                return

    @staticmethod
    def save_sms_history(
        *,
        created_by: Optional[User],
        created_for: Optional[User],
        phone_number: str,
        message: str,
        sms_type: str,
        status: str = QUEUE,
    ) -> SMSHistory:
        """
        Save SMSHistory using service.

        Args:
            created_by: User who initiated the SMS.
            created_for: User who is the recipient.
            phone_number: Recipient's phone number.
            message: SMS content.
            sms_type: Type of SMS.
            status: Delivery status.

        Returns:
            SMSHistory instance.
        """
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

    @staticmethod
    def update_sms_status(
        sms_history: SMSHistory,
        status: str,
        failed_reason: Optional[str] = None,
        failed_status_code: Optional[str] = None,
        response_at: Optional[Any] = now()
    ) -> None:
        """
        Update SMSHistory status.

        Args:
            sms_history: SMSHistory instance.
            status: New status.
            failed_reason: Reason for failure.
            failed_status_code: Status code for failure.
            response_at: Response timestamp.
        """
        sms_history.status = status
        sms_history.failed_reason = failed_reason
        sms_history.failed_status_code = failed_status_code
        sms_history.response_at = response_at
        sms_history.save()