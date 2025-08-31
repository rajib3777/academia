from django.urls import path, include
from rest_framework.routers import DefaultRouter
from student.views import (SchoolViewSet, SchoolNameListAPIView, StudentListCreateAPIView, StudentRetrieveUpdateDestroyAPIView, 
                           StudentCreateView, StudentUpdateView, StudentListView)

school_router = DefaultRouter()
school_router.register(r'schools', SchoolViewSet, basename='school')

school_urlpatterns = [
    path('', include(school_router.urls)),
]

student_urlpatterns = [
    path('students/', StudentListCreateAPIView.as_view(), name='student-list-create'),
    path('v1/students/create/', StudentCreateView.as_view(), name='student_create'),
    path('v1/students/<str:student_id>/update/', StudentUpdateView.as_view(), name='student_update'),
    path('v1/students/', StudentListView.as_view(), name='student_list'),
    path('student/<int:pk>/', StudentRetrieveUpdateDestroyAPIView.as_view(), name='student-detail'),
]

# Public (with auth) routes
public_urlpatterns = [
    path('school-name-list/', SchoolNameListAPIView.as_view(), name='public-school-name-list'),
]

urlpatterns = school_urlpatterns + student_urlpatterns + public_urlpatterns
