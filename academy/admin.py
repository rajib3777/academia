from django.contrib import admin
from django import forms
from academy.models import Academy, Course, Batch, BatchEnrollment, Grade
from classmate.admin import ClassMateAdmin
from academy.forms import AcademyAdminForm, CourseAdminForm, StudentPaymentInlineForm, BatchEnrollmentAdminForm
from payment.models import StudentPayment


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
    list_display = ('name', 'academy_id', 'contact_number', 'user')
    list_filter = ('user', 'name',)
    search_fields = ('name', 'user__username', 'contact_number', 'user__email', 'user__first_name', 'user__last_name', 'academy_id', 'user__phone',)
    autocomplete_fields = ('user',)
    ordering = ('name',)
    inlines = [CourseInline]
    form = AcademyAdminForm

    fields = [
        ('user', 'name', 'contact_number', ),
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
    list_display = ('name', 'course_id', 'fee', 'course_type', 'academy')
    list_filter = ('academy', 'course_type',)
    autocomplete_fields = ('academy',)
    search_fields = ('name', 'academy__name')
    ordering = ('name',)
    inlines = [BatchInline]
    form = CourseAdminForm
    date_hierarchy = 'created_at'  # Works only on: DateField or DateTimeField.
    # This will add a date filter on the right side of the admin page
    # to filter the list of objects by date.
    # It will show the date hierarchy based on the created_at field.
    # You can change 'created_at' to any DateField or DateTimeField in your model.

    fields = [('academy', 'name', 'fee', 'course_type', 'description')]
    

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
    list_display = ('name', 'batch_id', 'course', 'slot_category', 'start_date', 'end_date')
    list_filter = ('is_active', 'course__academy', 'course', 'slot_category', 'start_date', 'end_date')
    search_fields = ('name', 'course__name')
    inlines = [BatchEnrollmentInline]
    ordering = ['-start_date']
    date_hierarchy = 'start_date'
    autocomplete_fields = ['course']


class StudentPaymentInline(admin.StackedInline):
    """
    Inline admin for StudentPayment in BatchEnrollmentAdmin.
    """
    model = StudentPayment
    form = StudentPaymentInlineForm
    extra = 0
    autocomplete_fields = ['student']
    readonly_fields = ('date',)

    fieldsets = (
        (None, {
            'fields': (
                ('student', 'amount', 'date', ),
                ('method', 'status', 'transaction_id', ),
                ('remarks',),
            ),
        }),
        ('Refund Information', {
            'fields': ((
                'is_refunded',
                'refund_date',
            ),),
            'classes': ('collapse',),
        }),
    )


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
    form = BatchEnrollmentAdminForm
    ordering = ['-enrollment_date']
    inlines = [StudentPaymentInline]
    date_hierarchy = 'enrollment_date'

    fieldsets = (
        (None, {
            'fields': (
                ('student', 'batch'),
                ('enrollment_date', 'completion_date'),
                ('is_active', 'attendance_percentage', 'final_grade'),
                'remarks',
            ),
        }),
    )

    formfield_overrides = {
        BatchEnrollment._meta.get_field('remarks'): {
            'widget': forms.Textarea(attrs={'rows': 2, 'cols': 40}),
        },
    }