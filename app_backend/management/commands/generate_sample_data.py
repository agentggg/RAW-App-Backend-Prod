from django.core.management.base import BaseCommand
from faker import Faker
from app_backend.models import CustomUser, PushToken, Project, ProjectDetails, ProjectReporting, ProjectExpense

fake = Faker()

class Command(BaseCommand):
    help = 'Generate sample data'

    def handle(self, *args, **kwargs):
        # Create 5 users
        for _ in range(5):
            CustomUser.objects.create(
                username=fake.user_name(),
                email=fake.email(),
                first_name=fake.first_name(),
                last_name=fake.last_name(),
            )

        # Create 5 push tokens
        for _ in range(5):
            PushToken.objects.create(
                username=CustomUser.objects.order_by('?').first(),
                push_token=fake.uuid4(),
                device_make=fake.company(),
                device_model=fake.word(),
            )

        # Create 5 projects
        for _ in range(5):
            project = Project.objects.create(
                name=fake.word(),
                flag=fake.word(),
                dueDate=fake.date(),
                shortDescription=fake.text(max_nb_chars=100),
                longDescription=fake.text(max_nb_chars=200),
                image=fake.image_url(),
                color=fake.color(),
                initation=fake.boolean(),
                planning=fake.boolean(),
                execution=fake.boolean(),
                live=fake.boolean(),
                completed=fake.boolean(),
                review=fake.boolean(),
                projectType=fake.word(),
                startDate=fake.date(),
            )
            project.watchers.set(CustomUser.objects.order_by('?')[:3])  # Add 3 random watchers

        # Create 20 project details
        for _ in range(20):
            ProjectDetails.objects.create(
                name=Project.objects.order_by('?').first(),
                deliverableName=fake.word(),
                deliverableDetails=fake.text(max_nb_chars=100),
                deliverableOwner=CustomUser.objects.order_by('?').first(),
                watchers=CustomUser.objects.order_by('?').first(),
                deliverableStatus=fake.word(),
            )

        # Create 30 project reporting entries
        for _ in range(30):
            ProjectReporting.objects.create(
                name=Project.objects.order_by('?').first(),
                notes=fake.text(max_nb_chars=100),
                comments=fake.text(max_nb_chars=100),
            )

        # Create 20 project expense entries
        for _ in range(20):
            ProjectExpense.objects.create(
                projectName=Project.objects.order_by('?').first(),
                cost=fake.random_int(min=100, max=1000),
                costName=fake.word(),
                color=fake.color(),
            )

        self.stdout.write(self.style.SUCCESS('Sample data created successfully.'))
