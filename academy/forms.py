from django import forms
from .models import Academy, Course

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