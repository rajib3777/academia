from django.db.models.signals import post_save, post_delete, post_migrate
from django.dispatch import receiver
import random
from django.db.utils import OperationalError, ProgrammingError
from .models import Role
from .utils import force_update_role_cache
from account.choices import ROLE_CHOICES

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

    # Populate roles
    try:
        for role_key, role_name in ROLE_CHOICES:
            obj, created = Role.objects.get_or_create(name=role_key)
            if created:
                print(f'Added Role: {role_name}')
    except (OperationalError, ProgrammingError):
        pass  # Avoid errors during first migrations

    try:
        # Create superuser if not exists
        superuser_username = "milon"
        superuser_password = "adminmilon"
        superuser_phone = "01787829893"

        if not User.objects.filter(username=superuser_username).exists():
            admin_role = Role.objects.get(name="admin")
            superuser = User.objects.create_superuser(
                username=superuser_username,
                password=superuser_password,
                phone=superuser_phone,
                role=admin_role
            )
            print(f'Superuser created: {superuser_username}')

        # Create academy if not exists
        academy_username = "test_academy"
        academy_password = "adminmilon"
        academy_phone = "01787829892"

        if not User.objects.filter(username=academy_username).exists():
            academy_role = Role.objects.get(name="academy")
            academy = User.objects.create_superuser(
                username=academy_username,
                password=academy_password,
                phone=academy_phone,
                is_superuser=False,
                is_staff=False,
                role=academy_role
            )
            print(f'Test academy created: {academy_username}')

        # Create student if not exists
        student_password = "adminmilon"

        def generate_random_phone():
            return "017" + "".join([str(random.randint(0, 9)) for _ in range(8)])

        starting_id = 5001

        for i in range(1, 100):
            student_username = f"test_student_{i}"
            student_phone = generate_random_phone()

            if not User.objects.filter(username=student_username).exists():
                student_role = Role.objects.get(name="student")
                student_user = User.objects.create_user(
                    id=starting_id + i - 1,  # starting from 5001
                    username=student_username,
                    password=student_password,
                    phone=student_phone,
                    is_superuser=False,
                    is_staff=False,
                    role=student_role
                )
                print(f"Student created: {student_username}, ID: {student_user.id}, Phone: {student_phone}")

    except (OperationalError, ProgrammingError):
        pass  # Avoid errors during first migrations