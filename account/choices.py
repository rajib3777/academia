
# 🚨 Conflict Role Rules
CONFLICT_ROLE_PAIRS = [
    ({"admin", "student"}, "A user cannot be both an admin and a student."),
    ({"academy", "staff"}, "A user cannot be both an academy owner and staff."),
    ({"teacher", "student"}, "A user cannot be both a teacher and a student."),
    ({"admin", "academy"}, "An admin cannot be an academy owner."),
]