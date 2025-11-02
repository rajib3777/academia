import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from functools import cached_property
from rest_framework_simplejwt.authentication import JWTAuthentication
from payment.selectors.student_payment_selector import PaymentMethodSelector, PaymentStatusSelector
from payment.serializers import student_payment_serializer
logger = logging.getLogger(__name__)

# Create your views here.
class PaymentMethodDropdownView(APIView):
    """
    View to list all available payment methods.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    serializer_class = student_payment_serializer.PaymentMethodDropdownSerializer

    @cached_property
    def payment_method_selector(self):
        """Lazy initialization of PaymentMethodSelector."""
        return PaymentMethodSelector()
    
    def get(self, request, format=None):
        """
        Get list of all available payment methods.
        
        Returns:
            Response with payment methods data
        """
        try:
            payment_methods = self.payment_method_selector.list_payment_methods()
            serializer = self.serializer_class(payment_methods, many=True)

            return Response({
                'count': len(payment_methods),
                'results': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Error in PaymentMethodDropdownView: {str(e)}")
            return Response(
                {"detail": "An error occurred while retrieving payment methods."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class PaymentStatusDropdownView(APIView):
    """
    View to list all available payment statuses.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    serializer_class = student_payment_serializer.PaymentStatusDropdownSerializer

    @cached_property
    def payment_status_selector(self):
        """Lazy initialization of PaymentStatusSelector."""
        return PaymentStatusSelector()
    
    def get(self, request, format=None):
        """
        Get list of all available payment statuses.
        
        Returns:
            Response with payment statuses data
        """
        try:
            payment_statuses = self.payment_status_selector.list_payment_statuses()
            serializer = self.serializer_class(payment_statuses, many=True)

            return Response({
                'count': len(payment_statuses),
                'results': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Error in PaymentStatusDropdownView: {str(e)}")
            return Response(
                {"detail": "An error occurred while retrieving payment statuses."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
