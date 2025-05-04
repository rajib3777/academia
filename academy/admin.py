from django.contrib import admin
from academy.models import Academy, Course, Batch
from classmate.admin import ClassMateAdmin
from academy.forms import AcademyAdminForm, CourseAdminForm


# Inline for Course inside Academy
class CourseInline(admin.StackedInline):
    model = Course
    form = CourseAdminForm
    extra = 1
    fields = [('name', 'description', 'fee')]
    show_change_link = True


@admin.register(Academy)
class AcademyAdmin(ClassMateAdmin):
    list_display = ('name', 'contact_number', 'email', 'owner')
    list_filter = ('owner', 'name',)
    search_fields = ('name', 'owner__username', 'contact_number', 'email')
    ordering = ('name',)
    inlines = [CourseInline]
    form = AcademyAdminForm

    fields = [
        ('owner', 'name', 'contact_number', 'email',),
        ('description', 'address',),
    ]


# Inline for Batch inside Course
class BatchInline(admin.TabularInline):
    model = Batch
    extra = 1  # Number of blank inlines to display
    fields = [('name', 'start_date', 'end_date')]
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
    

@admin.register(Batch)
class BatchAdmin(ClassMateAdmin):
    list_display = ('name', 'course', 'start_date', 'end_date')
    list_filter = ('course',)
    search_fields = ('name', 'course__name')
    ordering = ('start_date',)
    date_hierarchy = 'start_date'

    fields = [('course', 'name', 'start_date', 'end_date')]