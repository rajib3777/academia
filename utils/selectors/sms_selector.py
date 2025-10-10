from utils.models import SMSHistory
from typing import Optional
from utils.choices import FAILED, SENT, QUEUE

class SMSHistorySelector:
    """
    Selector for SMSHistory ORM reads.
    """

    @staticmethod
    def get_queue_sms() -> Optional[SMSHistory]:
        return SMSHistory.objects.filter(status=QUEUE)

    @staticmethod
    def get_failed_sms() -> Optional[SMSHistory]:
        return SMSHistory.objects.filter(status=FAILED)

    @staticmethod
    def get_sent_sms() -> Optional[SMSHistory]:
        return SMSHistory.objects.filter(status=SENT)

    @staticmethod
    def get_by_id(sms_id: int) -> Optional[SMSHistory]:
        return SMSHistory.objects.filter(id=sms_id).first()

    @staticmethod
    def list_by_user(user_id: int):
        return SMSHistory.objects.filter(created_by_id=user_id).order_by('-created_at')