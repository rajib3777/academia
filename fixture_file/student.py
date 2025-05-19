import json

data = []
for i in range(99):
    student = {
        "model": "student.Student",
        "pk": 7001 + i,  # Start PK from 7001
        "fields": {
            "user": 5001 + i,
            "school": 6001 + (i // 33),
            "enrollment_date": "2024-01-01",
            "date_of_birth": f"2010-01-{(i % 28) + 1:02d}",
            "guardian_name": f"Guardian {i + 1}",
            "guardian_contact": f"017{i:08d}",
            "guardian_email": f"guardian{i + 1}@example.com",
            "guardian_relationship": "Parent",
            "address": f"Address of student {i + 1}",
            "batches": []
        }
    }
    data.append(student)

with open("student_fixture.json", "w") as f:
    json.dump(data, f, indent=2)
