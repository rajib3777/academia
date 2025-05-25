from .models import Student

def generate_student_id(prefix: str = "STD") -> str:
    count = Student.objects.count() + 1
    padded_number = str(count).zfill(6)
    return f"{prefix}-{padded_number}"
