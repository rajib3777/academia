from django.urls import path
from payment.apis import student_payment_apis
from payment import views

student_urlpatterns = [
    path('student/payments/', student_payment_apis.StudentPaymentListView.as_view(), name='student-payment-list'),
    path('student/payments/create/', student_payment_apis.StudentPaymentCreateView.as_view(), name='student-payment-create'),
    path('student/payments/<int:payment_id>/details/', student_payment_apis.StudentPaymentDetailView.as_view(), name='student-payment-detail'),
    path('student/payments/<int:payment_id>/update/', student_payment_apis.StudentPaymentUpdateView.as_view(), name='student-payment-update'),
    path('student/payments/<int:payment_id>/delete/', student_payment_apis.StudentPaymentDeleteView.as_view(), name='student-payment-delete'),
]


dropdown_urlpatterns = [
    path('payments/methods/dropdown/', views.PaymentMethodDropdownView.as_view(), name='payment-method-dropdown'),
    path('payments/statuses/dropdown/', views.PaymentStatusDropdownView.as_view(), name='payment-status-dropdown'),
]

urlpatterns = student_urlpatterns + dropdown_urlpatterns