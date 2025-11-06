import logging
import pytz
from typing import Optional, Any, Dict
from django.utils import timezone
from datetime import datetime, date, time
from classmate.utils import convert_date_to_dhaka
from django.core.exceptions import ValidationError
from payment.models import StudentPayment

logger = logging.getLogger(__name__)

class StudentPaymentService:

    @staticmethod
    def _combine_date_with_current_time(date_value: Any) -> datetime:
        """
        Combines a date with the current time to create a datetime object.
        Handles both date strings and date objects.
        """
        if isinstance(date_value, str):
            try:
                parsed_date = datetime.strptime(date_value, '%Y-%m-%d').date()
            except ValueError:
                raise ValidationError(f'Invalid date format. Expected YYYY-MM-DD, got: {date_value}')
        elif isinstance(date_value, date):
            parsed_date = date_value
        elif isinstance(date_value, datetime):
            # If already datetime, extract date and combine with current time
            parsed_date = date_value.date()
        else:
            raise ValidationError(f'Invalid date type. Expected string, date, or datetime, got: {type(date_value)}')
        
        # Get Dhaka timezone
        dhaka_tz = pytz.timezone('Asia/Dhaka')
        
        # Get current time in Dhaka timezone
        now_dhaka = timezone.now().astimezone(dhaka_tz)
        
        # Create datetime with current Dhaka time but specified date
        combined_datetime = dhaka_tz.localize(
            datetime.combine(parsed_date, now_dhaka.time())
        )
    
        return combined_datetime

    """
    Service for StudentPayment business logic and write operations.
    """
    @staticmethod
    def create_student_payment(data: Dict[str, Any]) -> StudentPayment:

        try:
            # Validate required fields
            required_fields = ['batch_enrollment_id', 'student_id', 'amount', 'method', 'status']
            for field in required_fields:
                if field not in data:
                    raise ValidationError(f'Missing required field: {field}')
                
            if data['amount'] <= 0:
                raise ValidationError('Amount must be greater than zero.')
            
            # Handle date - combine provided date with current time, or use current datetime
            payment_datetime = timezone.now()  # Default to current datetime
            if 'date' in data and data['date']:
                payment_datetime = StudentPaymentService._combine_date_with_current_time(data['date'])
                
            return StudentPayment.objects.create(
                batch_enrollment_id=data['batch_enrollment_id'],
                student_id=data['student_id'],
                amount=data['amount'],
                date=payment_datetime,
                method=data['method'],
                status=data['status'],
                transaction_id=data.get('transaction_id', ''),
                reference=data.get('reference', ''),
                remarks=data.get('remarks', ''),
                is_refunded=data.get('is_refunded', False),
                refund_date=data.get('refund_date'),
                metadata=data.get('metadata', {})
            )
            
            # Additional validation can be added here (e.g., amount > 0, valid method/status, etc.)
        except ValidationError as e:
            logger.exception(f"Error in create_student_payment: {str(e)}")
            raise ValidationError(f"Invalid data: {str(e)}")
        except Exception as e:
            logger.exception(f"Unexpected error in create_student_payment: {str(e)}")
            raise e


    @staticmethod
    def update_student_payment(payment: StudentPayment, payment_data: Dict[str, Any]) -> StudentPayment:
        try:
            # Store original date to check if it's being updated
            original_date = convert_date_to_dhaka(payment.date) if payment.date else None

            for field in [
                'amount', 'method', 'status', 'transaction_id', 'reference',
                'remarks', 'is_refunded', 'refund_date', 'metadata'
            ]:
                if field in payment_data:
                    setattr(payment, field, payment_data[field])

            # Handle date field separately
            if 'date' in payment_data and payment_data['date']:
                new_date_value = payment_data['date']

                # Extract date for comparison
                if isinstance(new_date_value, str):
                    try:
                        new_date = datetime.strptime(new_date_value, '%Y-%m-%d').date()
                    except ValueError:
                        raise ValidationError(f'Invalid date format. Expected YYYY-MM-DD, got: {new_date_value}')
                elif isinstance(new_date_value, date):
                    new_date = new_date_value.date()
                elif isinstance(new_date_value, datetime):
                    new_date = new_date_value.date()
                else:
                    raise ValidationError(f'Invalid date type. Expected string, date, or datetime, got: {type(new_date_value)}')
                
                # Only update if the date has actually changed
                if original_date != str(new_date):
                    payment.date = StudentPaymentService._combine_date_with_current_time(new_date_value)
            
            payment.save()
            return payment
        except ValidationError as e:
            logger.exception(f"Error in update_student_payment: {str(e)}")
            raise ValidationError(f"Invalid data: {str(e)}")
        except Exception as e:
            logger.exception(f"Unexpected error in update_student_payment: {str(e)}")
            raise e

    @staticmethod
    def delete_student_payment(payment: StudentPayment) -> None:
        payment.delete()