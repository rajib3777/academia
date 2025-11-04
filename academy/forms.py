from django import forms
from academy.models import Academy, Course, BatchEnrollment
from payment.models import StudentPayment

class AcademyAdminForm(forms.ModelForm):
    class Meta:
        model = Academy
        fields = '__all__'
        widgets = {
            'address': forms.Textarea(attrs={'rows': 2, 'cols': 72}),
        }


class CourseAdminForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2, 'cols': 72}),
        }


class BatchEnrollmentAdminForm(forms.ModelForm):
    class Meta:
        model = BatchEnrollment
        fields = '__all__'
        widgets = {
            'remarks': forms.Textarea(attrs={'rows': 2, 'cols': 72}),
        }


class StudentPaymentInlineForm(forms.ModelForm):
    class Meta:
        model = StudentPayment
        fields = '__all__'
        widgets = {
            'remarks': forms.Textarea(attrs={'rows': 2, 'cols': 60}),
        }