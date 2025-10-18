from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from academy.serializers.batch_enrollment_serializers import BatchEnrollmentSerializer
from academy.selectors.batch_enrollment_selector import BatchEnrollmentSelector
from academy.services.batch_enrollment_service import BatchEnrollmentService
from django.core.exceptions import ValidationError

class BatchEnrollmentListAPI(APIView):
    """
    API for listing batch enrollments with role-based and filter logic.
    """
    selector = BatchEnrollmentSelector()

    def get(self, request):
        filters = {
            'academy_id': request.GET.get('academy_id'),
            'course_id': request.GET.get('course_id'),
            'course_type': request.GET.get('course_type'),
            'batch_id': request.GET.get('batch_id'),
            'batch_start_date': request.GET.get('batch_start_date'),
            'batch_end_date': request.GET.get('batch_end_date'),
            'batch_is_active': request.GET.get('batch_is_active'),
            'enrollment_date': request.GET.get('enrollment_date'),
            'completion_date': request.GET.get('completion_date'),
            'is_active': request.GET.get('is_active'),
            'final_grade': request.GET.get('final_grade'),
        }
        # Only accept known keys
        filters = {k: v for k, v in filters.items() if v is not None}
        search = request.GET.get('search')
        enrollments = self.selector.list_enrollments(request.user, filters, search)
        serializer = BatchEnrollmentSerializer(enrollments, many=True)
        
        response_data = {
                'success': True,
                'data': serializer.data,
                'total_count': len(enrollments),
            }
            
        return Response(response_data, status=status.HTTP_200_OK)
        

class BatchEnrollmentCreateAPI(APIView):
    """
    API for creating batch enrollments. Only admin and academy can create.
    """
    service = BatchEnrollmentService()
    serializer_class = BatchEnrollmentSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            enrollment = self.service.create(request.user, serializer.validated_data)
            return Response(self.serializer_class(enrollment).data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_403_FORBIDDEN)


class BatchEnrollmentUpdateAPI(APIView):
    """
    API for updating a batch enrollment.
    """
    selector = BatchEnrollmentSelector()
    service = BatchEnrollmentService()
    serializer_class = BatchEnrollmentSerializer

    def put(self, request, enrollment_id: int):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            updated = self.service.update(request.user, enrollment_id, serializer.validated_data)
            return Response(self.serializer_class(updated).data, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_403_FORBIDDEN)
        

class BatchEnrollmentDetailAPI(APIView):
    """
    API for retrieving a batch enrollment.
    """
    selector = BatchEnrollmentSelector()
    serializer_class = BatchEnrollmentSerializer

    def get(self, request, enrollment_id: int):
        enrollment = self.selector.get_by_id(enrollment_id)
        if not enrollment:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.serializer_class(enrollment)
        return Response(serializer.data, status=status.HTTP_200_OK)
        

class BatchEnrollmentDeleteAPI(APIView):
    """
    API for deleting a batch enrollment.
    """
    service = BatchEnrollmentService()

    def delete(self, request, enrollment_id: int):
        try:
            self.service.delete(request.user, enrollment_id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValidationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_403_FORBIDDEN)