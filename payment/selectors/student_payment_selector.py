from typing import Optional, Any, Tuple, Dict, List
from django.core.paginator import Paginator
from account.models import User
from django.db.models import QuerySet, Q
from payment.models import StudentPayment
from payment.choices import PAYMENT_METHOD_CHOICES, PAYMENT_STATUS_CHOICES, PAYMENT_STATUS_PAID
class StudentPaymentSelector:
    """
    Selector for StudentPayment ORM read operations.
    """

    @staticmethod
    def get_by_id(payment_id: int) -> Optional[StudentPayment]:
        try:
            return StudentPayment.objects.select_related('student', 'batch_enrollment').get(id=payment_id)
        except StudentPayment.DoesNotExist:
            return None

    @staticmethod
    def all_student_payments() -> QuerySet:
        """
        Get all payments.
        """
        return StudentPayment.objects.select_related('student', 'batch_enrollment').all()


    @staticmethod
    def apply_list_permission_filtering(queryset: QuerySet, request_user) -> QuerySet:
        """
        Apply permission-based filtering to the queryset.
        - Academy users see all payments for their academy's batches.
        - Students see only their own payments.
        - Admins see all payments.
        - Others see no payments.
        """

        if request_user.is_admin():
            return queryset

        if request_user.is_academy():
            return queryset.filter(
                batch_enrollment__batch__course__academy=request_user.academy
            )

        if request_user.is_student():
            return queryset.filter(student=request_user.student)

        # Default: no access
        return queryset.none()

    @staticmethod
    def apply_list_filters(queryset: QuerySet, filters: Dict[str, Any]) -> QuerySet:
        """
        Apply filtering to the queryset based on provided filters.
        
        Args:
            queryset: The base queryset to filter
            filters: Dictionary of filter parameters
            
        Returns:
            Filtered queryset
        """
        method = filters.get('method', None)
        status = filters.get('status', None)
        is_refunded = filters.get('is_refunded', None)
        amount__gte = filters.get('amount__gte', None)
        amount__lte = filters.get('amount__lte', None)
        date__gte = filters.get('date__gte', None)
        date__lte = filters.get('date__lte', None)
        refund_date__gte = filters.get('refund_date__gte', None)
        refund_date__lte = filters.get('refund_date__lte', None)

        if method is not None:
            queryset = queryset.filter(method=method)

        if status is not None:
            queryset = queryset.filter(status=status)

        if is_refunded is not None:
            queryset = queryset.filter(is_refunded=is_refunded)

        if date__gte is not None:
            queryset = queryset.filter(date__gte=date__gte)

        if date__lte is not None:
            queryset = queryset.filter(date__lte=date__lte)

        if refund_date__gte is not None:
            queryset = queryset.filter(refund_date__gte=refund_date__gte)
        
        if refund_date__lte is not None:
            queryset = queryset.filter(refund_date__lte=refund_date__lte)

        if amount__gte is not None:
            queryset = queryset.filter(amount__gte=amount__gte)

        if amount__lte is not None:
            queryset = queryset.filter(amount__lte=amount__lte)

        return queryset
    
    @staticmethod
    def apply_list_search(queryset, search_query):
        """Apply search across multiple fields"""

        if search_query:
            queryset = queryset.filter(
                Q(batch_enrollment__batch__name__icontains=search_query) |
                Q(student_user_first_name__icontains=search_query) |
                Q(student_user_last_name__icontains=search_query) |
                Q(student__student_id__exact=search_query)
            ).distinct()

        return queryset
    

    @staticmethod
    def apply_list_ordering(queryset, ordering):
        """Apply ordering with multiple fields support"""
        ordering = ordering or '-date'

        # Define allowed ordering fields
        allowed_fields = [
            'id', 'date', 'is_refunded', 
        ]
        
        # Handle multiple ordering fields
        if ordering:
            order_fields = [field.strip() for field in ordering.split(',')]
            valid_fields = []
            
            for field in order_fields:
                # Remove '-' prefix for validation
                field_name = field.lstrip('-')
                if field_name in allowed_fields:
                    valid_fields.append(field)
            
            if valid_fields:
                return queryset.order_by(*valid_fields)
        
        # Default ordering
        return queryset.order_by('-date')
    

    @staticmethod
    def paginate_queryset(queryset, page_size, page):
        """Apply pagination"""
        page_size = int(page_size)
        page_number = int(page)
        
        # Limit page size to prevent abuse
        page_size = min(page_size, 20)
        
        paginator = Paginator(queryset, page_size)
        page = paginator.get_page(page_number)
        
        return {
            'results': page.object_list,
            'pagination': {
                'page': page_number,
                'page_size': page_size,
                'total_pages': paginator.num_pages,
                'total_items': paginator.count,
                'has_next': page.has_next(),
                'has_previous': page.has_previous(),
                'next_page': page.next_page_number() if page.has_next() else None,
                'previous_page': page.previous_page_number() if page.has_previous() else None,
            }
        }
    
    @staticmethod
    def list_payments(
        request_user: User,
        filters: Dict[str, Any] = None,
        search_query: Optional[str] = None,
        ordering: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
        ) -> Tuple[QuerySet, Dict[str, Any]]:

        # Get base queryset with optimized joins
        queryset = StudentPaymentSelector.all_student_payments()

        # Apply permission filtering
        queryset = StudentPaymentSelector.apply_list_permission_filtering(queryset, request_user)

        # Apply filters
        queryset = StudentPaymentSelector.apply_list_filters(queryset, filters)

        # Apply search
        queryset = StudentPaymentSelector.apply_list_search(queryset, search_query)

        # Apply ordering
        queryset = StudentPaymentSelector.apply_list_ordering(queryset, ordering)

        # Apply pagination
        paginated_data = StudentPaymentSelector.paginate_queryset(queryset, page_size, page)

        return paginated_data
    

class PaymentMethodSelector:
    """
    Selector for payment method choices.

    This selector provides methods to retrieve payment method data
    from the predefined choices.
    """
    
    @staticmethod
    def list_payment_methods() -> List[Dict[str, str]]:
        """
        Get all available payment methods.

        Returns:
            List of dictionaries with payment method values and display names
        """
        return [
            {'id': value, 'name': display_name} 
            for value, display_name in PAYMENT_METHOD_CHOICES
        ]
    

class PaymentStatusSelector:
    """
    Selector for payment status choices.

    This selector provides methods to retrieve payment status data
    from the predefined choices.
    """
    
    @staticmethod
    def list_payment_statuses() -> List[Dict[str, str]]:
        """
        Get all available payment statuses.

        Returns:
            List of dictionaries with payment status values and display names
        """
        # return [
        #     {'id': value, 'name': display_name} 
        #     for value, display_name in PAYMENT_STATUS_CHOICES
        # ]
        return [
            {'id': PAYMENT_STATUS_PAID, 'name': 'Paid'},
        ]
        