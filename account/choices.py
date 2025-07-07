
# 🚨 Conflict Role Rules
CONFLICT_ROLE_PAIRS = [
    ({"admin", "student"}, "A user cannot be both an admin and a student."),
    ({"admin", "academy"}, "An admin cannot be an academy owner."),
    ({"admin", "staff"}, "An admin cannot be a staff."),
    ({"admin", "teacher"}, "An admin cannot be a teacher."),
    ({"academy", "student"}, "A user cannot be both a academy and a student."),
    ({"academy", "teacher"}, "A user cannot be both a academy and a teacher."),
    ({"teacher", "student"}, "A user cannot be both a teacher and a student."),
    ({"staff", "student"}, "A user cannot be both a staff and a student."),
]

ADMIN = 'admin'
STUDENT = 'student'
ACADEMY = 'academy'

ROLE_CHOICES = [
    (ADMIN, 'Admin'),
    (STUDENT, 'Student'),
    (ACADEMY, 'Academy'),
]