YEAR_CHOICES = [
    (str(year), str(year))
    for year in range(2000, 2041)
]

# SUBJECT type choices
SUBJECT_TYPE_BANGLA = 'bangla'
SUBJECT_TYPE_ENGLISH = 'english'
SUBJECT_TYPE_MATHEMATICS = 'mathematics'
SUBJECT_TYPE_BIOLOGY = 'biology'
SUBJECT_TYPE_PHYSICS = 'physics'
SUBJECT_TYPE_CHEMISTRY = 'chemistry'
SUBJECT_TYPE_INFORMATION_AND_COMMUNICATIONS_TECHNOLOGY = 'ict'
SUBJECT_TYPE_PHYSICS_AND_CHEMISTRY = 'physics_and_chemistry'
SUBJECT_TYPE_EXAM_PREPARATION = 'exam_preparation'
SUBJECT_TYPE_BANGLA_1ST_AND_2ND = 'bangla_1st_and_2nd'
SUBJECT_TYPE_OTHERS = 'others'

SUBJECT_TYPE_CHOICES = [
    (SUBJECT_TYPE_BANGLA, 'Bangla'),
    (SUBJECT_TYPE_ENGLISH, 'English'),
    (SUBJECT_TYPE_MATHEMATICS, 'Mathematics'),
    (SUBJECT_TYPE_BIOLOGY, 'Biology'),
    (SUBJECT_TYPE_PHYSICS, 'Physics'),
    (SUBJECT_TYPE_CHEMISTRY, 'Chemistry'),
    (SUBJECT_TYPE_INFORMATION_AND_COMMUNICATIONS_TECHNOLOGY, 'Information and Communications Technology'),
    (SUBJECT_TYPE_PHYSICS_AND_CHEMISTRY, 'Physics and Chemistry'),
    (SUBJECT_TYPE_EXAM_PREPARATION, 'Exam Preparation'),
    (SUBJECT_TYPE_BANGLA_1ST_AND_2ND, 'Bangla 1st and 2nd'),
    (SUBJECT_TYPE_OTHERS, 'Others'),
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