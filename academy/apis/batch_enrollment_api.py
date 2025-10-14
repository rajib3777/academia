from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from academy.serializers.batch_enrollment_serializers import BatchEnrollmentSerializer
from academy.selectors.batch_enrollment_selector import BatchEnrollmentSelector
from academy.services.batch_enrollment_service import BatchEnrollmentService
from django.core.exceptions import ValidationError

class BatchEnrollmentListAPI(APIView):
    """
    API for listing batch enrollments.
    """
    selector = BatchEnrollmentSelector()
    service = BatchEnrollmentService()

    def get(self, request):
        filters = {
            'batch_id': request.GET.get('batch_id'),
            'student_id': request.GET.get('student_id'),
            'is_active': request.GET.get('is_active'),
        }
        enrollments = self.selector.list_enrollments(filters)
        serializer = BatchEnrollmentSerializer(enrollments, many=True)
        return Response(serializer.data)
        

class BatchEnrollmentCreateAPI(APIView):
    """
    API for creating batch enrollments.
    """
    selector = BatchEnrollmentSelector()
    service = BatchEnrollmentService()

    def post(self, request):
        serializer = BatchEnrollmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            enrollment = self.service.create(serializer.validated_data)
            return Response(BatchEnrollmentSerializer(enrollment).data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class BatchEnrollmentDetailAPI(APIView):
    """
    API for retrieving, updating, and deleting a batch enrollment.
    """
    selector = BatchEnrollmentSelector()
    service = BatchEnrollmentService()

    def get(self, request, enrollment_id):
        enrollment = self.selector.get_by_id(enrollment_id)
        if not enrollment:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = BatchEnrollmentSerializer(enrollment)
        return Response(serializer.data)

    def put(self, request, enrollment_id):
        enrollment = self.selector.get_by_id(enrollment_id)
        if not enrollment:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = BatchEnrollmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            updated = self.service.update(enrollment_id, serializer.validated_data)
            return Response(BatchEnrollmentSerializer(updated).data)
        except ValidationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, enrollment_id):
        enrollment = self.selector.get_by_id(enrollment_id)
        if not enrollment:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        self.service.delete(enrollment_id)
        return Response(status=status.HTTP_204_NO_CONTENT)