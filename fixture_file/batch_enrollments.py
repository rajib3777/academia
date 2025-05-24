import json
import random
from datetime import date, timedelta

# Constants
start_id = 11001
student_ids = list(range(7001, 7100))  # 7001 to 7099 inclusive
batch_ids = list(range(100001, 100016))  # 15 batches

# Remarks pool
remarks = [
    "Excellent performance",
    "Good improvement",
    "Consistent student",
    "Needs more practice",
    "Strong understanding of concepts",
    "Highly motivated learner"
]

# Helper to get value cyclically from a list
def get_cyclic(lst, idx):
    return lst[idx % len(lst)]

# Grade ID range: 33001 to 33007
grade_ids = list(range(33001, 33008))

# Update the enrollment list to use grade IDs instead of string grades
final_batch_enrollments = []
for i, student_id in enumerate(student_ids):
    batch_id = batch_ids[i % len(batch_ids)]
    enrollment_date = date(2025, 1, 1) + timedelta(days=random.randint(0, 60))  # Random Jan-Feb 2025 date
    enrollment = {
        "model": "academy.BatchEnrollment",
        "pk": start_id + i,
        "fields": {
            "student": student_id,
            "batch": batch_id,
            "enrollment_date": str(enrollment_date),
            "completion_date": str(date(2025, 7, 1)),
            "is_active": True,
            "attendance_percentage": f"{round(85 + (i % 15) * 0.8, 2):.2f}",
            "final_grade": random.choice(grade_ids),
            "remarks": get_cyclic(remarks, i)
        }
    }
    final_batch_enrollments.append(enrollment)

# Save final version of the fixture
final_file_path = "7_batch_enrollments_fixture.json"
with open(final_file_path, "w") as f:
    json.dump(final_batch_enrollments, f, indent=2)

final_file_path
