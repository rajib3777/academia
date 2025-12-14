from django.db import models
from account.models import User
from django.db.models.signals import pre_save
from django.dispatch import receiver
from classmate.models import ClassMateModel


class School(models.Model):
    name = models.CharField(max_length=255, unique=True)
    eiin = models.PositiveIntegerField(null=True, blank=True)
    address = models.TextField()
    email = models.EmailField(null=True, blank=True)
    contact_number = models.CharField(max_length=50, null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    logo = models.ImageField(upload_to='school_logos/', null=True, blank=True)

    def __str__(self):
        return self.name

class Student(ClassMateModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, limit_choices_to={'role__name': 'student'}, related_name='student')
    profile_picture = models.ImageField(upload_to='student_profiles/', null=True, blank=True, help_text="Upload a profile picture for the student")
    school = models.ForeignKey(School, on_delete=models.PROTECT)
    student_id = models.CharField(max_length=20, unique=True, help_text="Unique ID for the student", editable=False, null=True, blank=True)
    birth_registration_number = models.CharField(max_length=50, null=True, blank=True, help_text="Unique birth registration number for the student")
    date_of_birth = models.DateField(null=True, blank=True)
    guardian_name = models.CharField(max_length=255, null=True, blank=True)  
    guardian_phone = models.CharField(max_length=20, null=True, blank=True)
    guardian_email = models.EmailField(null=True, blank=True)
    guardian_relationship = models.CharField(max_length=50, null=True, blank=True)
    address = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username
    
    class Meta:
        verbose_name = "Student"
        verbose_name_plural = "Students"
        ordering = ['id']
        indexes = [
            models.Index(fields=['student_id']),
            models.Index(fields=['school_id']),
        ]


from django.db import models
from django.core.exceptions import ValidationError
import pandas as pd
from io import BytesIO

class TempSchool(models.Model):    
    # Excel upload field for importing participant data
    excel_upload = models.FileField(
        upload_to='temp_schools/uploads/', 
        verbose_name="Upload Excel for Participants",
        null=True,
        blank=True,
        help_text="Upload Excel file with columns: Name, Department, Score"
    )


    class Meta:
        verbose_name = "Temp School"
        verbose_name_plural = "Temp Schools"

    def save(self, *args, **kwargs):
        self.process_excel_file()

    def process_excel_file(self):
        """Process the uploaded Excel file and create School records"""

        # Read Excel file from the file object, not path
        self.excel_upload.seek(0)
        df = pd.read_excel(BytesIO(self.excel_upload.read()))

        required_columns = ['eiin', 'name', 'address', 'mobile']

        # Normalize column names
        df.columns = df.columns.str.strip().str.lower()

        # Check required columns
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValidationError(
                f"Missing required columns: {', '.join(missing_columns)}. "
                f"Excel should have columns: eiin, name, address, mobile"
            )

        participants_created = 0

        for index, row in df.iterrows():
            # Skip invalid rows
            if (
                pd.isna(row['name']) or str(row['name']).strip() == '' or
                pd.isna(row['eiin']) or str(row['eiin']).strip() == ''
            ):
                continue

            # ---- FIX FOR EIIN FLOAT ISSUE ----
            eiin_raw = str(row['eiin']).strip()
            eiin = int(eiin_raw.split('.')[0])  # take only integer part
            # ---------------------------------

            name = str(row['name']).strip()
            address = str(row['address']).strip() if not pd.isna(row['address']) else ''
            mobile = str(row['mobile']).strip() if not pd.isna(row['mobile']) else ''

            if mobile and not mobile.startswith('0'):
                mobile = '0' + mobile

            school, created = School.objects.update_or_create(
                eiin=eiin,
                defaults={
                    'name': name,
                    'address': address,
                    'contact_number': mobile[:15],
                }
            )

            if created:
                participants_created += 1

        print(f"Successfully imported {participants_created} participants from Excel")



@receiver(pre_save, sender=Student)
def set_student_id_on_create(sender, instance, **kwargs):
    """
    Signal to auto-generate student_id only when creating a new Student.
    """
    from student.utils import generate_student_id

    if (not instance.pk and not instance.student_id) or (instance.pk and not instance.student_id):
        instance.student_id = generate_student_id(instance)