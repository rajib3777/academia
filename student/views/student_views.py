import logging
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from student.models import School, Student
from rest_framework import generics
from rest_framework.filters import SearchFilter
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from utils.utils import verify_live_and_recovery_otp
from utils.choices import ACCOUNT
from django.core.exceptions import ValidationError
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from student.serializers.student_serializers import (SchoolNameListSerializer, StudentSerializer, 
                                 StudentCreateSerializer, StudentUpdateSerializer, StudentListSerializer, 
                                 StudentDetailSerializer, StudentDropdownSerializer,
                                 StudentAccountUpdateSerializer, StudentAccountDetailSerializer)
from student.serializers import student_serializers
from classmate.permissions import AuthenticatedGenericView
from classmate.utils import StandardResultsSetPagination, check_student_signup_rate_limit
from functools import cached_property
from student.selectors import student_selector
from student.services import student_service
logger = logging.getLogger(__name__)


class SchoolNameListAPIView(AuthenticatedGenericView, generics.ListAPIView):
    serializer_class = SchoolNameListSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [SearchFilter]
    search_fields = ['name', 'address', 'email', 'contact_number']
    queryset = School.objects.all()


class StudentActivateView(APIView):
    """API endpoint to activate a deactivated student."""
    
    @cached_property
    def student_service(self) -> student_service.StudentService:
        """Lazy initialization of StudentService."""
        return student_service.StudentService()

    def post(self, request, student_id):
        """
        Activate a deactivated student.
        """
        try:
            student = self.student_service.activate_student(student_id)
            serializer = StudentDetailSerializer(student)
            return Response(serializer.data)
        except ValidationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class StudentDeactivateView(APIView):
    """API endpoint to deactivate a student."""
    
    @cached_property
    def student_service(self) -> student_service.StudentService:
        """Lazy initialization of StudentService."""
        return student_service.StudentService()

    def post(self, request, student_id):
        """
        Deactivate a student.
        """
        try:
            student = self.student_service.deactivate_student(student_id)
            serializer = StudentDetailSerializer(student)
            return Response(serializer.data)
        except ValidationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class StudentCreateOldView(APIView):
    #TODO Remove this view after testing
    """
    Class-based view for creating students using StudentCreateSerializer
    """
    permission_classes = [IsAuthenticated]
    serializer_class = StudentCreateSerializer

    @transaction.atomic
    def post(self, request):
        """
        Create a new student with associated user account.
        
        Expected JSON payload:
        {
            "username": "john_doe_2024",
            "email": "john.doe@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "password": "securepassword123",
            "school": 1,
            "birth_registration_number": "BR123456789",
            "date_of_birth": "2010-05-15",
            "guardian_name": "Jane Doe",
            "guardian_phone": "+1234567890",
            "guardian_email": "jane.doe@example.com",
            "guardian_relationship": "Mother",
            "address": "123 Main St, City, State 12345"
        }
        """
        
        try:
            # Initialize serializer with request data
            serializer = self.serializer_class(data=request.data)
            
            # Validate the data
            if not serializer.is_valid():
                return Response(
                    {
                        'success': False,
                        'error': 'Validation failed',
                        'details': serializer.errors
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Save the student (creates both User and Student)
            student = serializer.save()
            
            # Serialize the created student for response
            response_serializer = StudentSerializer(student)
            
            return Response(
                {
                    'success': True,
                    'message': 'Student created successfully',
                    'data': response_serializer.data,
                    'student_id': student.student_id
                },
                status=status.HTTP_201_CREATED
            )
            
        except ValidationError as e:
            return Response(
                {
                    'success': False,
                    'error': 'Validation error',
                    'details': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        except Exception as e:
            return Response(
                {
                    'success': False,
                    'error': 'Failed to create student',
                    'details': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_serializer_class(self):
        """Return the serializer class to use"""
        return self.serializer_class

    def get_serializer(self, *args, **kwargs):
        """Return the serializer instance"""
        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        return serializer_class(*args, **kwargs)

    def get_serializer_context(self):
        """Extra context provided to the serializer class"""
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        }



class StudentUpdateOldView(APIView):
    #TODO Remove this view after testing
    """
    Class-based view for updating students using StudentUpdateSerializer
    """
    permission_classes = [IsAuthenticated]
    serializer_class = StudentUpdateSerializer

    def get_student(self, student_id):
        """Get student by ID or student_id"""
        try:
            # Try to get by primary key first
            if student_id.isdigit():
                return Student.objects.get(pk=student_id)
            else:
                # Try to get by student_id
                return Student.objects.get(student_id=student_id)
        except Student.DoesNotExist:
            return None

    @transaction.atomic
    def put(self, request, student_id):
        """
        Full update of student record
        
        Expected JSON payload:
        {
            "username": "updated_username",
            "email": "updated@example.com",
            "first_name": "Updated",
            "last_name": "Name",
            "school": 2,
            "birth_registration_number": "BR987654321",
            "date_of_birth": "2010-06-20",
            "guardian_name": "Updated Guardian",
            "guardian_phone": "+9876543210",
            "guardian_email": "guardian@example.com",
            "guardian_relationship": "Father",
            "address": "Updated Address"
        }
        """
        
        # Get student instance
        student = self.get_student(student_id)
        if not student:
            return Response(
                {
                    'success': False,
                    'error': 'Student not found'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            # Initialize serializer with instance and request data
            serializer = self.serializer_class(student, data=request.data)
            
            # Validate the data
            if not serializer.is_valid():
                return Response(
                    {
                        'success': False,
                        'error': 'Validation failed',
                        'details': serializer.errors
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Save the updated student
            updated_student = serializer.save()
            
            # Serialize the updated student for response
            response_serializer = StudentSerializer(updated_student)
            
            return Response(
                {
                    'success': True,
                    'message': 'Student updated successfully',
                    'data': response_serializer.data
                },
                status=status.HTTP_200_OK
            )
            
        except ValidationError as e:
            return Response(
                {
                    'success': False,
                    'error': 'Validation error',
                    'details': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        except Exception as e:
            return Response(
                {
                    'success': False,
                    'error': 'Failed to update student',
                    'details': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class StudentCreateView(APIView):
    """Create a new student."""
    # permission_classes = [IsAuthenticated]
    # authentication_classes = [JWTAuthentication]
    authentication_classes = []
    permission_classes = []
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service_class = student_service.StudentService()
        self.selector_class = student_selector.StudentSelector()

    def post(self, request, format=None):
        """
        Create a new student with user data.

        Returns:
            Response with created student data or error details
        """
        serializer = student_serializers.StudentCreateUpdateSerializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            try:
                serializer.is_valid(raise_exception=True)
                student = self.service_class.create_student(serializer.validated_data)

                # Get the created student with all related data for response
                detailed_student = self.selector_class.get_student_by_id(student.id)
                response_serializer = student_serializers.StudentListSerializer(detailed_student)

                return Response({'success': True, 'data': response_serializer.data}, status=status.HTTP_201_CREATED)
            
            except ValidationError as e:
                logger.error(f"Validation error in StudentCreateView: {str(e)}")
                return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
            except Exception as e:
                logger.error(f"Error in StudentCreateView: {str(e)}")
                return Response({'detail': str(e)},
                               status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StudentSignupView(APIView):
    """Create a new student."""
    authentication_classes = []
    permission_classes = []
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service_class = student_service.StudentService()
        self.selector_class = student_selector.StudentSelector()

    def post(self, request, format=None):
        # Check student signup rate limit
        check_student_signup_rate_limit(request)

        serializer = student_serializers.StudentSignUpSerializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            # Verify OTP
            otp_code = serializer.validated_data.pop('otp')
            verify_live_and_recovery_otp(serializer.validated_data['phone'], otp_code)

            try:
                student = self.service_class.student_signup(serializer.validated_data)
                return Response({'success': True, 'data': student}, status=status.HTTP_201_CREATED)
            
            except ValidationError as e:
                logger.error(f"Validation error in StudentCreateView: {str(e)}")
                return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
            except Exception as e:
                logger.error(f"Error in Student Signup View: {str(e)}")
                return Response({'detail': str(e)},
                               status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class StudentUpdateView(APIView):
    """Update an existing student."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service_class = student_service.StudentService()
        self.selector_class = student_selector.StudentSelector()

    def put(self, request, student_id, format=None):
        """
        Update a student and its associated user.

        Args:
            student_id: ID of the student to update

        Returns:
            Response with updated student data or error details
        """
        try:
            # Get the student first to check permissions
            student = self.selector_class.get_student_by_id(student_id)

            if not student:
                return Response({'detail': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)

            # Check if user is allowed to update this student
            if not request.user.is_superuser and not request.user.is_admin() and not request.user.is_student():
                return Response({'detail': 'You do not have permission to update this student'},
                                status=status.HTTP_403_FORBIDDEN)

            # Update the student
            serializer = student_serializers.StudentCreateUpdateSerializer(data=request.data, partial=True)

            if serializer.is_valid():
                try:
                    updated_student = self.service_class.update_student(student_id, serializer.validated_data)

                    if updated_student:
                        # Get the updated student with all related data for response
                        detailed_student = self.selector_class.get_student_by_id(student_id)
                        response_serializer = student_serializers.StudentListSerializer(detailed_student)
                        return Response(response_serializer.data)

                    return Response({'detail': 'Failed to update student'},
                                    status=status.HTTP_400_BAD_REQUEST)

                except ValidationError as e:
                    return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Error in StudentUpdateView: {str(e)}")
            return Response({'detail': 'An error occurred while updating the student.'},
                            status=status.HTTP_400_BAD_REQUEST)


class StudentDetailAPIView(APIView):
    """API endpoint for detailed student information and operations."""
    
    @cached_property
    def student_selector(self) -> student_selector.StudentSelector:
        """Lazy initialization of StudentSelector."""
        return student_selector.StudentSelector()
    
    def get(self, request, student_id):
        """
        Get detailed information for a specific student.
        """
        # Use selector to get optimized student data
        student = self.student_selector.get_student_by_id(student_id)
        
        if not student:
            return Response(
                {"detail": "Student not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Serialize and return the data
        serializer = StudentDetailSerializer(student)
        return Response(serializer.data)


class StudentListView(APIView):
    """
    Advanced Student List API with filtering, searching, ordering, and pagination.
    Uses a selector pattern to retrieve students based on various criteria.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    serializer_class = student_serializers.StudentListSerializer
    
    @cached_property
    def student_selector(self) -> student_selector.StudentSelector:
        """Lazy initialization of StudentSelector."""
        return student_selector.StudentSelector()
    
    def get(self, request):
        """
        Get filtered, searched, and ordered list of students
        
        Query Parameters:
        - Filter: school, school_name, username, email, first_name, last_name, etc.
        - Search: search=query (searches across multiple fields)
        - Ordering: ordering=field1,-field2 (comma-separated, - for desc)
        - Pagination: page=1&page_size=20
        - Date Range: date_of_birth_from=2010-01-01&date_of_birth_to=2015-12-31
        - Age Range: age_from=10&age_to=15
        - Boolean: has_guardian_email=true, is_active=false
        - Multiple: schools=1,2,3
        """
        try:
            # Extract pagination parameters
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 20))
            
            # Extract search and ordering parameters
            search_query = request.GET.get('search', '').strip()
            ordering = request.GET.get('ordering')
            academy_id = request.GET.get('academy_id')

            # Use selector to get data with all parameters
            pagination_info = self.student_selector.list_students(
                request_user=request.user,
                academy_id=academy_id,
                filters=request.GET,
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
            logger.exception("Error in StudentListView")
            
            return Response(
                {
                    'success': False,
                    'error': 'Failed to retrieve students',
                    'details': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class StudentDropdownView(APIView):
    """
    API endpoint for student dropdown data with role-based filtering.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def get(self, request):
        """
        Get filtered students for dropdown selection.
        
        Query parameters:
        - academy_id: Optional filter by specific academy ID
        - search: Optional search term for student name or ID
        """
        try:
            # Extract query parameters
            academy_id = request.query_params.get('academy_id')
            search = request.query_params.get('search')
            
            # Validate numeric parameters
            if academy_id and not academy_id.isdigit():
                return Response(
                    {"detail": "Academy ID must be a valid integer."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Convert parameters to appropriate types
            academy_id = int(academy_id) if academy_id else None

            # Get students using selector with role-based filtering
            students = student_selector.StudentSelector().get_students_for_dropdown(
                user=request.user,
                academy_id=academy_id,
                search=search
            )

            # Serialize and return the data
            serializer = StudentDropdownSerializer(students, many=True)
            return Response({
                'success': True,
                'data': serializer.data,
                'count': len(serializer.data)
            })
        
        except ValidationError as e:
            return Response(
                {
                    'success': False,
                    'error': 'Invalid parameters',
                    'details': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            # Log the exception
            import logging
            logger = logging.getLogger(__name__)
            logger.exception("Error in StudentDropdownView")
            
            return Response(
                {
                    'success': False,
                    'error': 'An unexpected error occurred',
                    'details': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class StudentEnrollmentDropdownView(APIView):
    """
    API endpoint for student dropdown data with role-based filtering.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def get(self, request):
        """
        Get filtered students for dropdown selection.
        
        Query parameters:
        - search: Optional search term for student name or ID
        """
        try:
            # Extract query parameters
            search = request.query_params.get('search')

            # Get students using selector with role-based filtering
            students = student_selector.StudentSelector().get_students_for_enrollment_dropdown(
                search=search
            )

            # Serialize and return the data
            serializer = StudentDropdownSerializer(students, many=True)
            return Response({
                'success': True,
                'data': serializer.data,
                'count': len(serializer.data)
            })
        
        except ValidationError as e:
            return Response(
                {
                    'success': False,
                    'error': 'Invalid parameters',
                    'details': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            # Log the exception
            import logging
            logger = logging.getLogger(__name__)
            logger.exception("Error in StudentEnrollmentDropdownView")
            
            return Response(
                {
                    'success': False,
                    'error': 'An unexpected error occurred',
                    'details': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class StudentDeleteView(APIView):
    """Delete a student."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service_class = student_service.StudentService()

    def delete(self, request, student_id, format=None):
        """
        Delete a student.

        Args:
            student_id: ID of the student to delete

        Returns:
            Response indicating success or failure
        """
        try:
            success = self.service_class.delete_student(student_id)

            if success:
                return Response(status=status.HTTP_204_NO_CONTENT)

            return Response({'detail': 'Student not found'},
                           status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            logger.error(f"Error in StudentDeleteView: {str(e)}")
            return Response({'detail': 'An error occurred while deleting the student.'},
                           status=status.HTTP_500_INTERNAL_SERVER_ERROR)