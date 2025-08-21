from django.contrib import admin
from academy.models import Academy, Course, Batch, BatchEnrollment, Grade
from classmate.admin import ClassMateAdmin
from academy.forms import AcademyAdminForm, CourseAdminForm


admin.site.register(Grade)

# Inline for Course inside Academy
class CourseInline(admin.StackedInline):
    model = Course
    form = CourseAdminForm
    extra = 1
    fields = [('name', 'description', 'fee')]
    show_change_link = True


@admin.register(Academy)
class AcademyAdmin(ClassMateAdmin):
    list_display = ('name', 'contact_number', 'email', 'user')
    list_filter = ('user', 'name',)
    search_fields = ('name', 'user__username', 'contact_number', 'email')
    ordering = ('name',)
    inlines = [CourseInline]
    form = AcademyAdminForm

    fields = [
        ('user', 'name', 'contact_number', 'email',),
        ('established_year', 'website', 'logo', 'description',),
        ('division', 'district', 'upazila', 'area_or_union', 'street_address', 'postal_code'),
    ]


# Inline for Batch inside Course
class BatchInline(admin.TabularInline):
    model = Batch
    extra = 1  # Number of blank inlines to display
    fields = [('name', 'start_date', 'end_date', 'is_active', 'description')]
    show_change_link = True


@admin.register(Course)
class CourseAdmin(ClassMateAdmin):
    list_display = ('name', 'fee', 'academy')
    list_filter = ('academy',)
    search_fields = ('name', 'academy__name')
    ordering = ('name',)
    inlines = [BatchInline]
    form = CourseAdminForm
    date_hierarchy = 'created_at'  # Works only on: DateField or DateTimeField.
    # This will add a date filter on the right side of the admin page
    # to filter the list of objects by date.
    # It will show the date hierarchy based on the created_at field.
    # You can change 'created_at' to any DateField or DateTimeField in your model.

    fields = [('academy', 'name', 'fee', 'description')]
    

class BatchEnrollmentInline(admin.TabularInline):
    model = BatchEnrollment
    extra = 0
    autocomplete_fields = ['student']
    fields = (
        'student',
        'enrollment_date',
        'completion_date',
        'is_active',
        'attendance_percentage',
        'final_grade',
        'remarks'
    )
    readonly_fields = ('enrollment_date',)


@admin.register(Batch)
class BatchAdmin(ClassMateAdmin):
    list_display = ('name', 'course', 'start_date', 'end_date')
    list_filter = ('course__academy', 'course', 'start_date', 'end_date')
    search_fields = ('name', 'course__name')
    inlines = [BatchEnrollmentInline]
    ordering = ['-start_date']
    date_hierarchy = 'start_date'
    autocomplete_fields = ['course']


@admin.register(BatchEnrollment)
class BatchEnrollmentAdmin(ClassMateAdmin):
    list_display = (
        'student',
        'batch',
        'enrollment_date',
        'completion_date',
        'is_active',
        'attendance_percentage',
        'final_grade'
    )
    list_filter = ('is_active', 'batch', 'enrollment_date', 'completion_date')
    search_fields = (
        'student__user__first_name',
        'student__user__last_name',
        'batch__name',
        'batch__course__name',
    )
    autocomplete_fields = ['student', 'batch']
    readonly_fields = ('enrollment_date',)
    ordering = ['-enrollment_date']