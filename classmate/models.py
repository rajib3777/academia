from django.db import models
from django.utils import timezone


class ClassMateModel(models.Model):
    created_by = models.ForeignKey(
        'account.User', on_delete=models.PROTECT, null=True, blank=True, related_name='%(class)s_created_by'
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    modified_by = models.CharField(max_length=100, null=True, blank=True)
    modified_at = models.DateTimeField(auto_now=True, null=True)
    archived_by = models.ForeignKey(
        'account.User', on_delete=models.PROTECT, null=True, blank=True, related_name='%(class)s_archived_by'
    )
    archived_at = models.DateTimeField(null=True, blank=True)
    is_archived = models.BooleanField(default=False)

    class Meta:
        abstract = True


def populate_user_info(request, instance, is_changed):
    if is_changed:
        instance.modified_at = timezone.now()
        instance.modified_by = str(request.user.id)
    else:
        instance.created_by = request.user