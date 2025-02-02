from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Role
from .utils import force_update_role_cache  # Import the function

@receiver(post_save, sender=Role)
@receiver(post_delete, sender=Role)
def refresh_role_cache(sender, **kwargs):
    """Update role cache automatically when Role model changes."""
    force_update_role_cache()
