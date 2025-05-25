from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from student.models import School
from rest_framework import generics
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from student.serializers import SchoolSerializer, SchoolNameListSerializer
from classmate.permissions import AuthenticatedGenericView
from classmate.utils import StandardResultsSetPagination

class SchoolViewSet(viewsets.ModelViewSet):
    queryset = School.objects.all()
    serializer_class = SchoolSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]


class SchoolNameListAPIView(AuthenticatedGenericView, generics.ListAPIView):
    serializer_class = SchoolNameListSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [SearchFilter]
    search_fields = ['name', 'address', 'email', 'contact_number']
    queryset = School.objects.all()