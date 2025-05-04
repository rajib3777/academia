from django.db.models.signals import post_save, post_delete, post_migrate
from django.dispatch import receiver
from django.db.utils import OperationalError, ProgrammingError
from .models import Role
from .utils import force_update_role_cache


@receiver(post_save, sender=Role)
@receiver(post_delete, sender=Role)
def refresh_role_cache(sender, **kwargs):
    """Update role cache automatically when Role model changes."""
    force_update_role_cache()


@receiver(post_migrate)
def populate_roles_and_superuser(sender, **kwargs):
    if sender.name != "account":  # Prevent running for other apps
        return

    from account.models import User, Role

    # Define role choices
    role_choices = [
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
        ('staff', 'Staff'),
        ('academy', 'Academy'),
    ]

    # Populate roles
    try:
        for role_key, role_name in role_choices:
            obj, created = Role.objects.get_or_create(name=role_key)
            if created:
                print(f'Added Role: {role_name}')
    except (OperationalError, ProgrammingError):
        pass  # Avoid errors during first migrations

    try:
        # Create superuser if not exists
        superuser_phone = "01787829893"
        superuser_username = "milon"
        superuser_password = "adminmilon"

        if not User.objects.filter(phone=superuser_phone).exists():
            superuser = User.objects.create_superuser(
                phone=superuser_phone,
                password=superuser_password,
                username=superuser_username
            )
            superuser.roles.add(Role.objects.get(name="admin"))  # Assign admin role
            print(f'Superuser created: {superuser_phone}')

    except (OperationalError, ProgrammingError):
        pass  # Avoid errors during first migrations