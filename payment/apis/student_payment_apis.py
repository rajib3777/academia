import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from payment.serializers import student_payment_serializer
from payment.selectors import student_payment_selector
from functools import cached_property
from payment.services import student_payment_service
logger = logging.getLogger(__name__)

class StudentPaymentCreateView(APIView):
    """
    API endpoint to create a Payment.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = student_payment_serializer.StudentPaymentSerializer

    def post(self, request):
        try:
            data = request.data.copy()
            data['created_by_id'] = request.user.id
            serializer = self.serializer_class(data=data)
            serializer.is_valid(raise_exception=True)

            payment = student_payment_service.StudentPaymentService.create_student_payment(serializer.validated_data)
            return Response(self.serializer_class(payment).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            # Log the exception
            logger.exception("Error in StudentPaymentCreateView")

            return Response(
                {
                    'success': False,
                    'error': 'Failed to create payment',
                    'details': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class StudentPaymentListView(APIView):
    """
    API endpoint to list Payments.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = student_payment_serializer.StudentPaymentSerializer

    @cached_property
    def payment_selector(self) -> student_payment_selector.StudentPaymentSelector:
        """Lazy initialization of PaymentSelector."""
        return student_payment_selector.StudentPaymentSelector()

    def get(self, request):
        try:
            # Extract pagination parameters
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 20))
            
            # Extract search and ordering parameters
            search_query = request.GET.get('search', '').strip()
            ordering = request.GET.get('ordering')

            pagination_info = self.payment_selector.list_payments(
                request_user=request.user,
                filters=request.GET,
                search_query=search_query,
                ordering=ordering,
                page=page,
                page_size=page_size
            )
            serializer = self.serializer_class(pagination_info['results'], many=True)

            # Build response
            response_data = {
                'success': True,
                'data': serializer.data,
                'pagination': pagination_info['pagination'],
                'filters_applied': dict(request.GET),
                'total_count': pagination_info['pagination']['total_items']
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            # Log the exception
            import logging
            logger = logging.getLogger(__name__)
            logger.exception("Error in PaymentListView")

            return Response(
                {
                    'success': False,
                    'error': 'Failed to retrieve payments',
                    'details': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class StudentPaymentDetailView(APIView):
    """
    API endpoint to retrieve a Payment.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = student_payment_serializer.StudentPaymentSerializer

    @cached_property
    def payment_selector(self) -> student_payment_selector.StudentPaymentSelector:
        """Lazy initialization of PaymentSelector."""
        return student_payment_selector.StudentPaymentSelector()

    def get(self, request, payment_id: int):
        payment = self.payment_selector.get_by_id(payment_id)
        if not payment:
            return Response({'detail': 'Student payment not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.serializer_class(payment)
        return Response(serializer.data)

class StudentPaymentUpdateView(APIView):
    """
    API endpoint to update a Payment.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = student_payment_serializer.StudentPaymentSerializer

    @cached_property
    def payment_selector(self) -> student_payment_selector.StudentPaymentSelector:
        """Lazy initialization of PaymentSelector."""
        return student_payment_selector.StudentPaymentSelector()

    def put(self, request, payment_id: int):
        try:
            payment = self.payment_selector.get_by_id(payment_id)
            if not payment:
                return Response({'detail': 'Student payment not found.'}, status=status.HTTP_404_NOT_FOUND)
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            payment = student_payment_service.StudentPaymentService.update_student_payment(payment, serializer.validated_data)
            return Response(self.serializer_class(payment).data)
        except Exception as e:
            logger.exception("Error in StudentPaymentUpdateView")
            return Response(
                {
                    'success': False,
                    'error': 'Failed to update payment',
                    'details': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

class StudentPaymentDeleteView(APIView):
    """
    API endpoint to delete a Payment.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @cached_property
    def payment_selector(self) -> student_payment_selector.StudentPaymentSelector:
        """Lazy initialization of PaymentSelector."""
        return student_payment_selector.StudentPaymentSelector()

    def delete(self, request, payment_id: int):
        payment = self.payment_selector.get_by_id(payment_id)
        if not payment:
            return Response({'detail': 'Student payment not found.'}, status=status.HTTP_404_NOT_FOUND)
        student_payment_service.StudentPaymentService.delete_student_payment(payment)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
