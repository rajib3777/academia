from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from student.models import School, Student
from rest_framework import generics
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.core.exceptions import ValidationError
from student.serializers import (SchoolSerializer, SchoolNameListSerializer, StudentSerializer, 
                                 StudentCreateSerializer, StudentUpdateSerializer, StudentListSerializer, 
                                 StudentDetailSerializer, StudentDropdownSerializer)
from classmate.permissions import AuthenticatedGenericView
from classmate.utils import StandardResultsSetPagination
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q
from django.core.paginator import Paginator
from student.utils import StudentFilter
from functools import cached_property
from student.selectors import student_selector
from student.services import student_service

class SchoolViewSet(viewsets.ModelViewSet):
    queryset = School.objects.all().order_by('id')
    serializer_class = SchoolSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]


class SchoolNameListAPIView(AuthenticatedGenericView, generics.ListAPIView):
    serializer_class = SchoolNameListSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [SearchFilter]
    search_fields = ['name', 'address', 'email', 'contact_number']
    queryset = School.objects.all()


class StudentListCreateAPIView(generics.ListCreateAPIView):
    queryset = Student.objects.all().order_by('id')
    serializer_class = StudentSerializer

# class StudentRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
#     queryset = Student.objects.all().order_by('id')
#     serializer_class = StudentSerializer
#     lookup_field = 'pk'

class StudentRetrieveUpdateDestroyAPIView(APIView):
    """API endpoint for detailed student information and operations."""
    
    @cached_property
    def student_selector(self) -> student_selector.StudentSelector:
        """Lazy initialization of StudentSelector."""
        return student_selector.StudentSelector()

    @cached_property
    def student_service(self) -> student_service.StudentService:
        """Lazy initialization of StudentService."""
        return student_service.StudentService()
    
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
    
    def patch(self, request, student_id):
        """
        Partially update a student's information.
        """
        try:
            # Extract user and student data from request
            user_data = {}
            student_data = {}
            
            # User fields
            for field in ['username', 'first_name', 'last_name', 'email', 'phone', 'password']:
                if field in request.data:
                    user_data[field] = request.data[field]
            
            # Student fields
            for field in ['school_id', 'birth_registration_number', 'date_of_birth', 
                         'guardian_name', 'guardian_phone', 'guardian_email', 
                         'guardian_relationship', 'address']:
                if field in request.data:
                    student_data[field] = request.data[field]
            
            # Update student using service
            student = self.student_service.update_student(
                student_id=student_id,
                user_data=user_data if user_data else None,
                student_data=student_data if student_data else None
            )
            
            # Return updated student data
            serializer = StudentDetailSerializer(student)
            return Response(serializer.data)
            
        except ValidationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def delete(self, request, student_id):
        """
        Deactivate a student (soft delete).
        """
        try:
            self.student_service.deactivate_student(student_id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValidationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


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
    

class StudentCreateView(APIView):
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



class StudentUpdateView(APIView):
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
        


class StudentListView(APIView):
    """
    Advanced Student List API with filtering, searching, and ordering
    """
    # Response format:
    """
        {
            "success": true,
            "data": [
                {
                    "id": 1,
                    "user": {
                        "id": 1,
                        "username": "john_doe",
                        "email": "john@example.com",
                        "first_name": "John",
                        "last_name": "Doe",
                        "full_name": "John Doe",
                        "is_active": true
                    },
                    "school": {
                        "id": 1,
                        "name": "ABC High School"
                    },
                    "student_id": "STU-2024-123456",
                    "birth_registration_number": "BR123456789",
                    "date_of_birth": "2010-05-15",
                    "age": 13,
                    "guardian_name": "Jane Doe",
                    "guardian_phone": "+1234567890",
                    "guardian_email": "jane@example.com",
                    "guardian_relationship": "Mother",
                    "address": "123 Main St",
                    "created_at": "2024-01-15T10:30:00Z",
                    "updated_at": "2024-01-15T10:30:00Z"
                }
            ],
            "pagination": {
                "page": 1,
                "page_size": 20,
                "total_pages": 5,
                "total_items": 95,
                "has_next": true,
                "has_previous": false,
                "next_page": 2,
                "previous_page": null
            },
            "filters_applied": {
                "school": ["1"],
                "search": ["john"],
                "age_from": ["10"],
                "age_to": ["15"]
            },
            "total_count": 95
        }
    """
    permission_classes = [IsAuthenticated]
    serializer_class = StudentListSerializer
    filterset_class = StudentFilter
    
    def get_queryset(self):
        """Get optimized queryset with select_related for performance"""
        return Student.objects.select_related('user', 'school').filter(user__is_active=True).order_by('id')

    def apply_filters(self, queryset, request):
        """Apply filters using django-filter"""
        filterset = self.filterset_class(request.GET, queryset=queryset)
        if filterset.is_valid():
            return filterset.qs
        return queryset
    
    def apply_search(self, queryset, request):
        """Apply search across multiple fields"""
        search_query = request.GET.get('search', '').strip()
        if search_query:
            return queryset.filter(
                Q(user__username__icontains=search_query) |
                Q(user__email__icontains=search_query) |
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(student_id__icontains=search_query) |
                Q(birth_registration_number__icontains=search_query) |
                Q(guardian_name__icontains=search_query) |
                Q(guardian_phone__icontains=search_query) |
                Q(guardian_email__icontains=search_query) |
                Q(address__icontains=search_query) |
                Q(school__name__icontains=search_query)
            )
        return queryset
    
    def apply_ordering(self, queryset, request):
        """Apply ordering with multiple fields support"""
        ordering = request.GET.get('ordering', '-created_at')
        
        # Define allowed ordering fields
        allowed_fields = [
            'id', 'student_id', 'created_at', 'modified_at', 'date_of_birth',
            'user__username', 'user__email', 'user__first_name', 'user__last_name',
            'school__name', 'guardian_name'
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
        return queryset.order_by('-created_at')
    
    def paginate_queryset(self, queryset, request):
        """Apply pagination"""
        page_size = int(request.GET.get('page_size', 20))
        page_number = int(request.GET.get('page', 1))
        
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
            # Get base queryset
            queryset = self.get_queryset()
            
            # Apply filters
            queryset = self.apply_filters(queryset, request)
            
            # Apply search
            queryset = self.apply_search(queryset, request)
            
            # Apply ordering
            queryset = self.apply_ordering(queryset, request)
            
            # Get total count before pagination
            total_count = queryset.count()
            
            # Apply pagination
            paginated_data = self.paginate_queryset(queryset, request)
            
            # Serialize data
            serializer = self.serializer_class(paginated_data['results'], many=True)
            
            # Build response
            response_data = {
                'success': True,
                'data': serializer.data,
                'pagination': paginated_data['pagination'],
                'filters_applied': dict(request.GET),
                'total_count': total_count
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
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
            selector = student_selector.StudentSelector()
            students = selector.get_students_for_dropdown(
                user=request.user,
                academy_id=academy_id,
                search=search
            )

            # Serialize and return the data
            serializer = StudentDropdownSerializer(students, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            # Log the exception
            import logging
            logger = logging.getLogger(__name__)
            logger.exception("Error in StudentDropdownView")
            
            return Response(
                {"detail": "An unexpected error occurred."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )