from rest_framework import generics
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.exceptions import ValidationError, NotFound, PermissionDenied
from django.shortcuts import get_object_or_404
from django.db.models import ProtectedError
from academy.models import Academy, Course, Batch
from academy.serializers import AcademySerializer, CourseSerializer, BatchSerializer, AcademyOwnerSerializer, CourseNameListSerializer
from classmate.permissions import AuthenticatedGenericView, IsSuperUserOrAdmin, IsAcademyOwner
from classmate.utils import StandardResultsSetPagination

# ----------- ACADEMY VIEWS -----------
class AcademyListCreateAPIView(AuthenticatedGenericView, IsSuperUserOrAdmin, generics.ListCreateAPIView):
    serializer_class = AcademySerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['name', 'owner__id', 'contact_number', 'email']
    search_fields = ['name', 'description', 'address', 'owner__username', 'email']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        queryset = Academy.objects.select_related('owner').all()

        # Optional: filter by query params like ?search=keyword
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(address__icontains=search) |
                Q(owner__username__icontains=search) |
                Q(email__icontains=search)
            )

        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def create(self, request, *args, **kwargs):
        """
        Override to customize response after creation.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.perform_create(serializer)

        return Response({
            'message': 'Academy created successfully!'
        }, status=status.HTTP_201_CREATED, headers=headers)


class AcademyRetrieveUpdateDestroyAPIView(AuthenticatedGenericView, IsSuperUserOrAdmin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AcademySerializer

    def get_queryset(self):
        """
        Optimized queryset with related owner.
        """
        return Academy.objects.select_related('owner').all()

    def get_object(self):
        """
        Custom get_object to handle not found or permission issues.
        """
        obj = get_object_or_404(self.get_queryset(), pk=self.kwargs.get('pk'))
        # Optionally restrict further, e.g., only owner can access
        if not self.request.user.is_admin() or not self.request.user.is_superuser:
            raise PermissionDenied("You don't have permission to access this academy.")
        return obj

    def update(self, request, *args, **kwargs):
        """
        Override to customize update validation and response.
        """
        partial = kwargs.pop('partial', False) 
        # Handles both PUT (full) and PATCH (partial) cases
        # partial=True	Allows updates with only some fields
        instance = self.get_object()
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

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
class CourseListCreateAPIView(AuthenticatedGenericView, IsAcademyOwner, generics.ListCreateAPIView):
    serializer_class = CourseSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return Course.objects.filter(
            academy__owner=self.request.user
        ).prefetch_related('batches')
    

    def perform_create(self, serializer):
        academy = self.request.user.academy.first()

        if not academy:
            raise ValidationError({"academy": "No academy is associated with this user."})
        
        if Course.objects.filter(academy=academy, name=self.request.data['name']).exists():
            raise ValidationError({
                'name': 'This course name already exists for this academy.'
            })
        serializer.save(academy=academy)


class CourseNameListAPIView(AuthenticatedGenericView, generics.ListAPIView):
    serializer_class = CourseNameListSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        academy = self.request.user.academy.first()
        if academy:
            return Course.objects.filter(academy=academy).values('id', 'name')
        return Course.objects.all().values('id', 'name')


class CourseRetrieveUpdateDestroyAPIView(AuthenticatedGenericView, IsAcademyOwner, generics.RetrieveUpdateDestroyAPIView):
    queryset = Course.objects.all().prefetch_related('batches')
    serializer_class = CourseSerializer


# ----------- BATCH VIEWS -----------
class BatchListCreateAPIView(AuthenticatedGenericView, generics.ListCreateAPIView):
    queryset = Batch.objects.all()
    serializer_class = BatchSerializer
    pagination_class = StandardResultsSetPagination


class BatchRetrieveUpdateDestroyAPIView(AuthenticatedGenericView, generics.RetrieveUpdateDestroyAPIView):
    queryset = Batch.objects.all()
    serializer_class = BatchSerializer
