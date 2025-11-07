from rest_framework.views import APIView
import logging
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from rest_framework import status
from functools import cached_property
from academy.serializers.batch_enrollment_serializers import BatchEnrollmentSerializer
from academy.selectors import batch_enrollment_selector
from academy.services.batch_enrollment_service import BatchEnrollmentService
from django.core.exceptions import ValidationError
from classmate.permissions import AuthenticatedGenericView
logger = logging.getLogger(__name__)

class BatchEnrollmentListAPI(AuthenticatedGenericView, APIView):
    """
    API for listing batch enrollments with role-based and filter logic.
    """
    serializer_class = BatchEnrollmentSerializer

    @cached_property
    def batch_enrollment_selector(self) -> batch_enrollment_selector.BatchEnrollmentSelector:
        """Lazy initialization of BatchEnrollmentSelector."""
        return batch_enrollment_selector.BatchEnrollmentSelector()

    def get(self, request):
        try:
            # Extract pagination parameters
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 20))

            # Extract search and ordering parameters
            search_query = request.GET.get('search', '').strip()
            ordering = request.GET.get('ordering')

            pagination_info = self.batch_enrollment_selector.list_enrollments(
                request_user=request.user,
                filters=request.GET.dict(),
                search_query=search_query,
                ordering=ordering,
                page=page,
                page_size=page_size
            )

            # Serialize data
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
            logger.exception("Error in BatchEnrollmentListAPI")
            return Response(
                {
                    'success': False,
                    'error': 'Failed to retrieve batch enrollments',
                    'details': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BatchEnrollmentCreateAPI(AuthenticatedGenericView, APIView):
    """
    API for creating batch enrollments. Only admin and academy can create.
    """
    service_class = BatchEnrollmentService()
    serializer_class = BatchEnrollmentSerializer

    def post(self, request):
        try:
            serializer = self.serializer_class(data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)

            # Extract data
            enrollment_data = {
                'student_id': serializer.validated_data['student_id'],
                'batch_id': serializer.validated_data['batch_id'],
                'is_active': serializer.validated_data['is_active'],
                'remarks': serializer.validated_data['remarks'],
                'discount_fee': serializer.validated_data['discount_fee']
            }

            payments_data = serializer.validated_data.get('payments', None)

            enrollment = self.service_class.create_enrollment(
                request_user=request.user,
                enrollment_data=enrollment_data,
                payments_data=payments_data
            )
            return Response({
                'success': True,
                'message': 'Student enrollment created successfully',
                'data': self.serializer_class(enrollment).data
            }, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            logger.exception(f"Error in BatchEnrollmentCreateAPI: {str(e)}")
            return Response({
                'success': False,
                'error': 'An unexpected error occurred'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BatchEnrollmentUpdateAPI(AuthenticatedGenericView, APIView):
    """
    API for updating a batch enrollment.
    """
    service_class = BatchEnrollmentService()
    selector_class = batch_enrollment_selector.BatchEnrollmentSelector()
    serializer_class = BatchEnrollmentSerializer

    def put(self, request, enrollment_id: int):
        try:
            enrollment = self.selector_class.get_by_id(enrollment_id)

            if not enrollment:
                return Response({
                        'success': False,
                        'error': 'Student enrollment not found'
                    }, status=status.HTTP_404_NOT_FOUND)
            
            serializer = self.serializer_class(data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)

            # Extract data
            enrollment_data = {
                'student_id': serializer.validated_data['student_id'],
                'batch_id': serializer.validated_data['batch_id'],
                'is_active': serializer.validated_data['is_active'],
                'discount_fee': serializer.validated_data['discount_fee'],
                'remarks': serializer.validated_data['remarks']
            }
            payments_data = serializer.validated_data.get('payments', None)
        
            updated = self.service_class.update_enrollment(
                request_user=request.user,
                enrollment=enrollment,
                enrollment_data=enrollment_data,
                payments_data=payments_data
            )
            return Response(self.serializer_class(updated).data, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_403_FORBIDDEN)
        

class BatchEnrollmentDetailAPI(AuthenticatedGenericView, APIView):
    """
    API for retrieving a batch enrollment.
    """
    selector = batch_enrollment_selector.BatchEnrollmentSelector()
    serializer_class = BatchEnrollmentSerializer

    def get(self, request, enrollment_id: int):
        enrollment = self.selector.get_by_id(enrollment_id)
        if not enrollment:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.serializer_class(enrollment)
        return Response(serializer.data, status=status.HTTP_200_OK)
        

class BatchEnrollmentDeleteAPI(AuthenticatedGenericView, APIView):
    """
    API for deleting a batch enrollment.
    """
    service_class = BatchEnrollmentService()

    def delete(self, request, enrollment_id: int):
        try:
            self.service_class.delete_enrollment(request.user, enrollment_id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValidationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_403_FORBIDDEN)