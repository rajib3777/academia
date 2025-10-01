from django.urls import path
from academy.views.academy_views import (
    AcademyListCreateAPIView, AcademyRetrieveUpdateDestroyAPIView,
    CourseListCreateAPIView, CourseRetrieveUpdateDestroyAPIView,
    BatchListCreateAPIView, BatchRetrieveUpdateDestroyAPIView, UpdateAcademyFromUserAPIView,
    AcademyDropdownView
)
from academy.views.course_views import CourseCreateView, CourseUpdateView, CourseListView, CourseDropdownView, CourseDeleteView
from academy.views.batch_views import BatchCreateView, BatchUpdateView, BatchListView, BatchDeleteView, BatchDropdownView


# Admin-only routes
admin_urlpatterns = [
    path('academies/', AcademyListCreateAPIView.as_view(), name='academy-list-create'),
    path('academy/<int:pk>/', AcademyRetrieveUpdateDestroyAPIView.as_view(), name='academy-detail'),
    path('academies/dropdown/', AcademyDropdownView.as_view(), name='academy-dropdown'),

]

# Academy-owner routes
academy_urlpatterns = [
    path('academy/my-academy/', UpdateAcademyFromUserAPIView.as_view(), name='academy-update-my-academy'),
    path('academy/courses/', CourseListCreateAPIView.as_view(), name='academy-course-list-create'),
    path('academy/courses/<int:pk>/', CourseRetrieveUpdateDestroyAPIView.as_view(), name='academy-course-detail'),
    path('academy/batches/', BatchListCreateAPIView.as_view(), name='academy-batch-list-create'),
    path('academy/batches/<int:pk>/', BatchRetrieveUpdateDestroyAPIView.as_view(), name='academy-batch-detail'),
]

course_urlpatterns = [
    # Course endpoints
    path('v1/courses/', CourseListView.as_view(), name='course-list'),
    path('v1/courses/create/', CourseCreateView.as_view(), name='course-create'),
    path('v1/courses/<int:course_id>/update/', CourseUpdateView.as_view(), name='course-update'),
    path('v1/courses/<int:course_id>/', CourseDeleteView.as_view(), name='course-delete'),
    path('courses/dropdown/', CourseDropdownView.as_view(), name='course-dropdown'),

]

batch_urlpatterns = [
    # Batch endpoints
    path('v1/batches/', BatchListView.as_view(), name='batch-list'),
    path('v1/batches/create/', BatchCreateView.as_view(), name='batch-create'),
    path('v1/batches/<int:batch_id>/update/', BatchUpdateView.as_view(), name='batch-update'),
    path('v1/batches/<int:batch_id>/', BatchDeleteView.as_view(), name='batch-delete'),
    path('batches/dropdown/', BatchDropdownView.as_view(), name='batch-dropdown'),

]

# Combine them into final urlpatterns
urlpatterns = admin_urlpatterns + academy_urlpatterns + course_urlpatterns + batch_urlpatterns
