from django.contrib.admin.helpers import ActionForm
from django import forms

class GenerateOTPActionForm(ActionForm):
    academy_id = forms.CharField(
        required=False,
        label="Academy ID",
        help_text="Example: AID-2025-0001"
    )
