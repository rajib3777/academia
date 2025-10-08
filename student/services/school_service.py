from student.models import School
from typing import Dict

class SchoolService:
    """
    Service for School business logic and writes.
    """

    def create_school(self, data: Dict) -> School:
        school = School.objects.create(**data)
        return school

    def update_school(self, school: School, data: Dict) -> School:
        for field, value in data.items():
            setattr(school, field, value)
        school.full_clean()
        school.save()
        return school

    def delete_school(self, school: School) -> None:
        school.delete()