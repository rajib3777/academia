YEAR_CHOICES = [
    (str(year), str(year))
    for year in range(2000, 2041)
]

# Course type choices
COURSE_TYPE_BANGLA = 'bangla'
COURSE_TYPE_ENGLISH = 'english'
COURSE_TYPE_MATHEMATICS = 'mathematics'
COURSE_TYPE_BIOLOGY = 'biology'
COURSE_TYPE_PHYSICS = 'physics'
COURSE_TYPE_CHEMISTRY = 'chemistry'
COURSE_TYPE_INFORMATION_AND_COMMUNICATIONS_TECHNOLOGY = 'ict'

COURSE_TYPE_CHOICES = [
    (COURSE_TYPE_BANGLA, 'Bangla'),
    (COURSE_TYPE_ENGLISH, 'English'),
    (COURSE_TYPE_MATHEMATICS, 'Mathematics'),
    (COURSE_TYPE_BIOLOGY, 'Biology'),
    (COURSE_TYPE_PHYSICS, 'Physics'),
    (COURSE_TYPE_CHEMISTRY, 'Chemistry'),
    (COURSE_TYPE_INFORMATION_AND_COMMUNICATIONS_TECHNOLOGY, 'Information and Communications Technology'),
]