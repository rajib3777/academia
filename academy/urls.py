from django.urls import path
from academy.views.academy_views import (
    AcademyListCreateAPIView, AcademyRetrieveUpdateDestroyAPIView,
    CourseListCreateAPIView, CourseRetrieveUpdateDestroyAPIView,
    BatchListCreateAPIView, BatchRetrieveUpdateDestroyAPIView, UpdateAcademyFromUserAPIView, CourseNameListAPIView,
    BatchNameListAPIView, AcademyDropdownView
)
from academy.views.course_views import CourseCreateView, CourseUpdateView, CourseListView, CourseDropdownView
from academy.views.batch_views import BatchCreateView, BatchUpdateView, BatchListView


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

# Public (with auth) routes
public_urlpatterns = [
    path('course-name-list/', CourseNameListAPIView.as_view(), name='public-course-name-list'),
    path('batch-name-list/', BatchNameListAPIView.as_view(), name='public-batch-name-list'),
]

course_urlpatterns = [
    # Course endpoints
    path('v1/courses/', CourseListView.as_view(), name='course-list'),
    path('v1/courses/create/', CourseCreateView.as_view(), name='course-create'),
    path('v1/courses/<int:course_id>/update/', CourseUpdateView.as_view(), name='course-update'),

]

batch_urlpatterns = [
    # Batch endpoints
    path('v1/batches/', BatchListView.as_view(), name='batch-list'),
    path('v1/batches/create/', BatchCreateView.as_view(), name='batch-create'),
    path('v1/batches/<int:batch_id>/update/', BatchUpdateView.as_view(), name='batch-update'),
]

dropdown_urlpatterns = [
    path('courses/dropdown/', CourseDropdownView.as_view(), name='course-dropdown'),
]

# Combine them into final urlpatterns
urlpatterns = admin_urlpatterns + academy_urlpatterns + public_urlpatterns + course_urlpatterns + batch_urlpatterns + dropdown_urlpatterns
