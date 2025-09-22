from rest_framework import generics
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError
from functools import cached_property
from rest_framework.exceptions import ValidationError, NotFound, PermissionDenied
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.shortcuts import get_object_or_404
from django.db.models import ProtectedError
from academy.models import Academy, Course, Batch
from academy.serializers.academy_serializers import (AcademySerializer, CourseSerializer, BatchSerializer, AcademyOwnerSerializer, 
                                 CourseNameListSerializer, BatchNameListSerializer, CourseCreateSerializer, AcademyDropdownSerializer)
from classmate.permissions import AuthenticatedGenericView, IsSuperUserOrAdmin, IsAcademyOwner
from classmate.utils import StandardResultsSetPagination
from academy.selectors import academy_selector

# ----------- ACADEMY VIEWS -----------
class AcademyListCreateAPIView(AuthenticatedGenericView, IsSuperUserOrAdmin, generics.ListCreateAPIView):
    serializer_class = AcademySerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['name', 'user__id', 'contact_number', 'email']
    search_fields = ['name', 'description', 'user__username', 'email']
    ordering_fields = ['name', 'created_at']
    ordering = ['id']

    def get_queryset(self):
        queryset = Academy.objects.select_related('user').all()

        # Optional: filter by query params like ?search=keyword
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(address__icontains=search) |
                Q(user__username__icontains=search) |
                Q(email__icontains=search)
            )

        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def create(self, request, *args, **kwargs):
        """
        Override to customize response after creation.
        """
        print('data: ', request.data)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.perform_create(serializer)

        return Response({
            'message': 'Academy created successfully!'
        }, status=status.HTTP_201_CREATED)


class AcademyRetrieveUpdateDestroyAPIView(AuthenticatedGenericView, generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsSuperUserOrAdmin]

    serializer_class = AcademySerializer

    def get_queryset(self):
        """
        Optimized queryset with related user.
        """
        return Academy.objects.select_related('user').all()

    def get_object(self):
        """
        Custom get_object to handle not found or permission issues.
        """
        obj = get_object_or_404(self.get_queryset(), pk=self.kwargs.get('pk'))
        return obj

    def update(self, request, *args, **kwargs):
        """
        Override to customize update validation and response.
        """
        partial = kwargs.pop('partial', False) 
        # Handles both PUT (full) and PATCH (partial) cases
        # partial=True	Allows updates with only some fields
        instance = self.get_object()
        print('sfsfs: ', instance)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        print('serializer', serializer)
        self.perform_update(serializer)
        
        return Response({
            'message': 'Academy updated successfully!'
        }, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        """
        Override to safely handle deletion (e.g., prevent deletion if related objects exist).
        """
        instance = self.get_object()
        try:
            print('xx', instance)
            self.perform_destroy(instance)
        except ProtectedError:
            return Response({
                'error': 'This academy cannot be deleted because it has related data (e.g., courses or batches).'
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'message': 'Academy deleted successfully.'
        }, status=status.HTTP_204_NO_CONTENT)


class UpdateAcademyFromUserAPIView(AuthenticatedGenericView, IsAcademyOwner, APIView):
    def put(self, request):
        try:
            academy = Academy.objects.get(owner=request.user)
        except Academy.DoesNotExist:
            return Response({'detail': 'Academy not found for this user.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = AcademyOwnerSerializer(academy, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

# ----------- COURSE VIEWS -----------
class CourseListCreateAPIView(AuthenticatedGenericView, generics.ListCreateAPIView):
    serializer_class = CourseCreateSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        # return Course.objects.filter(
        #     academy__owner=self.request.user
        # ).prefetch_related('batches')
        return Course.objects.all().order_by('id').prefetch_related('batches')

    def perform_create(self, serializer):
        academy = self.request.user.academy.first()

        if not academy:
            raise serializers.ValidationError({"academy": "No academy is associated with this user."})
        serializer.save(academy=academy)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request  # optional, DRF includes it by default
        return context


class CourseRetrieveUpdateDestroyAPIView(AuthenticatedGenericView, IsAcademyOwner, generics.RetrieveUpdateDestroyAPIView):
    queryset = Course.objects.all().prefetch_related('batches')
    serializer_class = CourseCreateSerializer


class CourseNameListAPIView(AuthenticatedGenericView, generics.ListAPIView):
    serializer_class = CourseNameListSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['name', 'academy__id']
    search_fields = ['name', 'description']

    def get_queryset(self):
        academy = self.request.user.academy.first()
        if academy:
            return Course.objects.filter(academy=academy).values('id', 'name')
        return Course.objects.all().order_by('id').values('id', 'name')
    
    
# ----------- BATCH VIEWS -----------
class BatchListCreateAPIView(AuthenticatedGenericView, generics.ListCreateAPIView):
    serializer_class = BatchSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user

        return Batch.objects.select_related(
            'course',
            'course__academy',
            'course__academy__user'
        ).prefetch_related(
            'students'
        ).filter(
            course__academy__user=user
        ).order_by('id')
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request  # optional, DRF includes it by default
        return context


class BatchRetrieveUpdateDestroyAPIView(AuthenticatedGenericView, generics.RetrieveUpdateDestroyAPIView):
    queryset = Batch.objects.all().prefetch_related('students')
    serializer_class = BatchSerializer


class BatchNameListAPIView(AuthenticatedGenericView, generics.ListAPIView):
    serializer_class = BatchNameListSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['name', 'course__id']
    search_fields = ['name', 'description']

    def get_queryset(self):
        academy = self.request.user.academy.first()
        if academy:
            return Batch.objects.filter(course__academy=academy).order_by('id').values('id', 'name')
        return Batch.objects.all().order_by('id').values('id', 'name')


class AcademyDropdownView(APIView):
    """
    API endpoint for academy dropdown data.
    Returns minimal data needed for dropdown selection.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]  # Use default authentication classes
    
    @cached_property
    def academy_selector(self) -> academy_selector.AcademySelector:
        """Lazy initialization of AcademySelector."""
        return academy_selector.AcademySelector()

    def get(self, request):
        """
        Get academy data for dropdown selection.
        
        Query parameters:
        - search: Optional search term for academy name
        - is_active: Filter by active status (default: true)
        """
        try:
            # Extract query parameters
            search = request.query_params.get('search', '')
            is_active = request.query_params.get('is_active', 'true').lower() == 'true'
            
            # Get academies using selector
            academies = self.academy_selector.get_academies_for_dropdown(
                search_query=search,
                request_user=request.user,
                is_active=is_active
            )
            
            # Serialize data
            serializer = AcademyDropdownSerializer(academies, many=True)
            
            # Return response
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
            logger.exception("Error in AcademyDropdownView")
            
            return Response(
                {
                    'success': False,
                    'error': 'An unexpected error occurred',
                    'details': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
