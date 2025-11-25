from django.urls import path, include
from rest_framework.routers import DefaultRouter
from student.views.student_views import (SchoolNameListAPIView, 
                           StudentCreateOldView, StudentCreateView,StudentUpdateView, StudentListView, StudentActivateView, StudentDropdownView, 
                           StudentDetailAPIView, StudentDeleteView)
from student.views.school_views import SchoolListView, SchoolCreateView, SchoolUpdateView, SchoolDeleteView, SchoolDropdownView, PublicSchoolListView

school_urlpatterns = [
    path('v1/schools/', SchoolListView.as_view(), name='school-list'),
    path('v1/schools/public/', PublicSchoolListView.as_view(), name='public-school-list'),
    path('v1/schools/create/', SchoolCreateView.as_view(), name='school-create'),
    path('v1/schools/<int:school_id>/update/', SchoolUpdateView.as_view(), name='school-update'),
    path('v1/schools/<int:school_id>/delete/', SchoolDeleteView.as_view(), name='school-delete'),

]

dropdown_urlpatterns = [
    path('students/dropdown/', StudentDropdownView.as_view(), name='student-dropdown'),
    path('schools/dropdown/', SchoolDropdownView.as_view(), name='school-dropdown'),
]

student_urlpatterns = [
    path('v1/students/', StudentListView.as_view(), name='student_list'),
    path('v1/students/create/', StudentCreateView.as_view(), name='student_create'),
    path('v1/students/<str:student_id>/update/', StudentUpdateView.as_view(), name='student_update'),
    path('v1/students/<str:student_id>/details/', StudentDetailAPIView.as_view(), name='student_details'),
    path('v1/students/<str:student_id>/delete/', StudentDeleteView.as_view(), name='student_delete'),
    path('v1/students/<str:student_id>/activate/', StudentActivateView.as_view(), name='student-activate'),
    path('v1/students/<str:student_id>/deactivate/', StudentActivateView.as_view(), name='student-deactivate'),

]

# Public (with auth) routes
public_urlpatterns = [
    path('school-name-list/', SchoolNameListAPIView.as_view(), name='public-school-name-list'),
]

urlpatterns = school_urlpatterns + student_urlpatterns + public_urlpatterns + dropdown_urlpatterns
