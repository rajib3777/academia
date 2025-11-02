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

JAN_JUN = 'jan-jun'
JUL_DEC = 'jul-dec'
JAN_APR = 'jan-apr'
MAY_AUG = 'may-aug'
SEP_DEC = 'sep-dec'
CUSTOM = 'custom'

SLOT_CATEGORY_CHOICES = [
    (JAN_JUN, 'January to June (6 Months)'),
    (JUL_DEC, 'July to December (6 Months)'),
    (JAN_APR, 'January to April (4 Months)'),
    (MAY_AUG, 'May to August (4 Months)'),
    (SEP_DEC, 'September to December (4 Months)'),
    (CUSTOM, 'Custom Slot'),
]