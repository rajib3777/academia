from django.urls import path
from academy.views import (
    AcademyListCreateAPIView, AcademyRetrieveUpdateDestroyAPIView,
    CourseListCreateAPIView, CourseRetrieveUpdateDestroyAPIView,
    BatchListCreateAPIView, BatchRetrieveUpdateDestroyAPIView, UpdateAcademyFromUserAPIView
)

urlpatterns = [
    path('academies/', AcademyListCreateAPIView.as_view(), name='academy-list-create'),
    path('academy/<int:pk>/', AcademyRetrieveUpdateDestroyAPIView.as_view(), name='academy-detail'),
    path('academy/update-my-academy/', UpdateAcademyFromUserAPIView.as_view(), name='update-my-academy'),

    path('courses/', CourseListCreateAPIView.as_view(), name='course-list-create'),
    path('courses/<int:pk>/', CourseRetrieveUpdateDestroyAPIView.as_view(), name='course-detail'),

    path('batches/', BatchListCreateAPIView.as_view(), name='batch-list-create'),
    path('batches/<int:pk>/', BatchRetrieveUpdateDestroyAPIView.as_view(), name='batch-detail'),
]
