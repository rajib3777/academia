from django.urls import path
from academy.apis.academy_views import (
    AcademyListCreateAPIView, AcademyRetrieveUpdateDestroyAPIView,
    CourseListCreateAPIView, CourseRetrieveUpdateDestroyAPIView,
    BatchListCreateAPIView, BatchRetrieveUpdateDestroyAPIView, UpdateAcademyFromUserAPIView,
    AcademyDropdownView
)
from academy.apis.academy_views_v2 import (AcademyListView, AcademyCreateView, AcademyDetailView, AcademyUpdateView, AcademyDeleteView, YearListAPIView)
from academy.apis.course_views import CourseCreateView, CourseUpdateView, CourseListView, CourseDropdownView, CourseDeleteView, SubjectDropdownView
from academy.apis.batch_views import BatchCreateView, BatchUpdateView, BatchListView, BatchDeleteView, BatchDropdownView
from academy.apis import batch_enrollment_api


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

academy_urlpatterns_v2 = [
    path('v1/academies/', AcademyListView.as_view(), name='academy-list'),
    path('v1/academies/create/', AcademyCreateView.as_view(), name='academy-create'),
    path('v1/academies/<int:academy_id>/update/', AcademyUpdateView.as_view(), name='academy-update'),
    path('v1/academies/<int:academy_id>/details/', AcademyDetailView.as_view(), name='academy-detail-for-admin'),
    path('v1/academies/details/', AcademyDetailView.as_view(), name='academy-detail-for-academy-user'),
    path('v1/academies/<int:academy_id>/delete/', AcademyDeleteView.as_view(), name='academy-delete'), # need to work here. user not deleting. also need to add soft delete feature
    path('year-choice/dropdown/', YearListAPIView.as_view(), name='year-choice-dropdown'),

]

course_urlpatterns = [
    # Course endpoints
    path('v1/courses/', CourseListView.as_view(), name='course-list'),
    path('v1/courses/create/', CourseCreateView.as_view(), name='course-create'),
    path('v1/courses/<int:course_id>/update/', CourseUpdateView.as_view(), name='course-update'),
    path('v1/courses/<int:course_id>/delete/', CourseDeleteView.as_view(), name='course-delete'),
    path('courses/dropdown/', CourseDropdownView.as_view(), name='course-dropdown'),
    path('subjects/dropdown/', SubjectDropdownView.as_view(), name='subject-dropdown'),

]

batch_urlpatterns = [
    # Batch endpoints
    path('v1/batches/', BatchListView.as_view(), name='batch-list'),
    path('v1/batches/create/', BatchCreateView.as_view(), name='batch-create'),
    path('v1/batches/<int:batch_id>/update/', BatchUpdateView.as_view(), name='batch-update'),
    path('v1/batches/<int:batch_id>/delete/', BatchDeleteView.as_view(), name='batch-delete'),
    path('batches/dropdown/', BatchDropdownView.as_view(), name='batch-dropdown'),

]

batch_enrollment_urlpatterns = [
    path('batch-enrollments/', batch_enrollment_api.BatchEnrollmentListAPI.as_view(), name='batch_enrollment_list'),
    path('batch-enrollments/create/', batch_enrollment_api.BatchEnrollmentCreateAPI.as_view(), name='batch_enrollment_create'),
    path('batch-enrollments/<int:enrollment_id>/update/', batch_enrollment_api.BatchEnrollmentUpdateAPI.as_view(), name='batch_enrollment_update'),
    path('batch-enrollments/<int:enrollment_id>/details/', batch_enrollment_api.BatchEnrollmentDetailAPI.as_view(), name='batch_enrollment_detail'),
    path('batch-enrollments/<int:enrollment_id>/delete/', batch_enrollment_api.BatchEnrollmentDeleteAPI.as_view(), name='batch_enrollment_delete'),
]

# Combine them into final urlpatterns
urlpatterns = admin_urlpatterns + academy_urlpatterns + academy_urlpatterns_v2 + course_urlpatterns + batch_urlpatterns + batch_enrollment_urlpatterns
