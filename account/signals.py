from django.db.models.signals import post_save, post_delete, post_migrate
from django.dispatch import receiver
import random
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
        superuser_username = "milon"
        superuser_password = "adminmilon"
        superuser_phone = "01787829893"

        if not User.objects.filter(username=superuser_username).exists():
            superuser = User.objects.create_superuser(
                username=superuser_username,
                password=superuser_password,
                phone=superuser_phone,
                
            )
            superuser.roles.add(Role.objects.get(name="admin"))  # Assign admin role
            print(f'Superuser created: {superuser_username}')

        # Create admin if not exists
        admin_username = "admin"
        admin_password = "adminmilon"
        admin_phone = "01787829891"

        if not User.objects.filter(username=admin_username).exists():
            admin = User.objects.create_superuser(
                username=admin_username,
                password=admin_password,
                phone=admin_phone,
                is_superuser=False,
                is_staff=True
            )
            admin.roles.add(Role.objects.get(name="admin"))  # Assign admin role
            print(f'Admin created: {admin_username}')

        # Create academy if not exists
        academy_username = "test_academy"
        academy_password = "adminmilon"
        academy_phone = "01787829892"

        if not User.objects.filter(username=academy_username).exists():
            academy = User.objects.create_superuser(
                username=academy_username,
                password=academy_password,
                phone=academy_phone,
                is_superuser=False,
                is_staff=False
            )
            academy.roles.add(Role.objects.get(name="academy"))  # Assign admin role
            print(f'Test academy created: {academy_username}')

        # Create teacher if not exists
        teacher_username = "test_teacher"
        teacher_phone = "01787829894"
        teacher_password = "adminmilon"

        if not User.objects.filter(username=teacher_username).exists():
            superuser = User.objects.create_superuser(
                username=teacher_username,
                password=teacher_password,
                phone=teacher_phone,
                is_superuser=False,
                is_staff=False
            )
            superuser.roles.add(Role.objects.get(name="teacher"))  # Assign teacher role
            print(f'Test teacher created: {teacher_username}')

        # Create student if not exists
        student_password = "adminmilon"

        def generate_random_phone():
            return "017" + "".join([str(random.randint(0, 9)) for _ in range(8)])

        starting_id = 5001

        for i in range(1, 100):
            student_username = f"test_student_{i}"
            student_phone = generate_random_phone()

            if not User.objects.filter(username=student_username).exists():
                student_user = User.objects.create_user(
                    id=starting_id + i - 1,  # starting from 5001
                    username=student_username,
                    password=student_password,
                    phone=student_phone,
                    is_superuser=False,
                    is_staff=False
                )
                student_user.roles.add(Role.objects.get(name="student"))
                print(f"Student created: {student_username}, ID: {student_user.id}, Phone: {student_phone}")

    except (OperationalError, ProgrammingError):
        pass  # Avoid errors during first migrations