from django.urls import path, include
from rest_framework.routers import DefaultRouter
from student.views import student_views
from student.views import school_views


school_urlpatterns = [
    path('v1/schools/', school_views.SchoolListView.as_view(), name='school-list'),
    path('v1/schools/public/', school_views.PublicSchoolListView.as_view(), name='public-school-list'),
    path('v1/schools/create/', school_views.SchoolCreateView.as_view(), name='school-create'),
    path('v1/schools/<int:school_id>/update/', school_views.SchoolUpdateView.as_view(), name='school-update'),
    path('v1/schools/<int:school_id>/delete/', school_views.SchoolDeleteView.as_view(), name='school-delete'),
]

dropdown_urlpatterns = [
    path('students/dropdown/', student_views.StudentDropdownView.as_view(), name='student-dropdown'),
    path('schools/dropdown/', school_views.SchoolDropdownView.as_view(), name='school-dropdown'),
]

student_urlpatterns = [
    path('v1/students/', student_views.StudentListView.as_view(), name='student_list'),
    path('v1/students/create/', student_views.StudentCreateView.as_view(), name='student_create'),
    path('v1/students/signup/', student_views.StudentSignupView.as_view(), name='student_signup'),
    path('v1/students/<str:student_id>/update/', student_views.StudentUpdateView.as_view(), name='student_update'),
    path('v1/students/<str:student_id>/details/', student_views.StudentDetailAPIView.as_view(), name='student_details'),
    path('v1/students/<str:student_id>/delete/', student_views.StudentDeleteView.as_view(), name='student_delete'),
    path('v1/students/<str:student_id>/activate/', student_views.StudentActivateView.as_view(), name='student-activate'),
    path('v1/students/<str:student_id>/deactivate/', student_views.StudentDeactivateView.as_view(), name='student-deactivate'),

]

# Public (with auth) routes
public_urlpatterns = [
    path('school-name-list/', student_views.SchoolNameListAPIView.as_view(), name='public-school-name-list'),
]

urlpatterns = school_urlpatterns + student_urlpatterns + public_urlpatterns + dropdown_urlpatterns
