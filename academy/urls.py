from django.urls import path
from academy.views import (
    AcademyListCreateAPIView, AcademyRetrieveUpdateDestroyAPIView,
    CourseListCreateAPIView, CourseRetrieveUpdateDestroyAPIView,
    BatchListCreateAPIView, BatchRetrieveUpdateDestroyAPIView, UpdateAcademyFromUserAPIView, CourseNameListAPIView,
    BatchNameListAPIView
)

# Admin-only routes
admin_urlpatterns = [
    path('academies/', AcademyListCreateAPIView.as_view(), name='academy-list-create'),
    path('academy/<int:pk>/', AcademyRetrieveUpdateDestroyAPIView.as_view(), name='academy-detail'),
]

# Academy-owner routes
academy_urlpatterns = [
    path('academy/my-academy/', UpdateAcademyFromUserAPIView.as_view(), name='academy-update-my-academy'),
    path('academy/courses/', CourseListCreateAPIView.as_view(), name='academy-course-list-create'),
    path('academy/courses/<int:pk>/', CourseRetrieveUpdateDestroyAPIView.as_view(), name='academy-course-detail'),
    path('academy/batches/', BatchListCreateAPIView.as_view(), name='academy-batch-list-create'),
    path('academy/batches/<int:pk>/', BatchRetrieveUpdateDestroyAPIView.as_view(), name='academy-batch-detail'),
]

# Public (with auth) routes
public_urlpatterns = [
    path('course-name-list/', CourseNameListAPIView.as_view(), name='public-course-name-list'),
    path('batch-name-list/', BatchNameListAPIView.as_view(), name='public-batch-name-list'),
]

# Combine them into final urlpatterns
urlpatterns = admin_urlpatterns + academy_urlpatterns + public_urlpatterns
